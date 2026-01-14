"""
Tests for PostgreSQL Batch Optimization.

Tests cover:
- BatchConfig validation and defaults
- Insert batching
- Update batching
- Upsert batching
- Delete batching
- Batch size limits
- Parameter limits
- Error handling
- Statistics tracking
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.performance.batch import (
    BatchConfig,
    BatchResult,
    BatchStats,
    BatchOptimizer,
    bulk_load_config,
    transactional_config,
    disabled_batch_config,
)


# =============================================================================
# BatchConfig Tests
# =============================================================================

class TestBatchConfig:
    """Tests for BatchConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = BatchConfig()
        assert config.enabled is True
        assert config.max_batch_size == 1000
        assert config.max_params == 65535
        assert config.batch_inserts is True
        assert config.batch_updates is True
        assert config.batch_upserts is True
        assert config.return_results is True
    
    def test_custom_batch_size(self):
        """Test custom batch size."""
        config = BatchConfig(max_batch_size=5000)
        assert config.max_batch_size == 5000
    
    def test_custom_max_params(self):
        """Test custom max_params."""
        config = BatchConfig(max_params=32000)
        assert config.max_params == 32000
    
    def test_zero_batch_size_raises(self):
        """Test that zero batch size raises error."""
        with pytest.raises(ValueError, match="max_batch_size must be >= 1"):
            BatchConfig(max_batch_size=0)
    
    def test_zero_max_params_raises(self):
        """Test that zero max_params raises error."""
        with pytest.raises(ValueError, match="max_params must be >= 1"):
            BatchConfig(max_params=0)
    
    def test_disabled_inserts(self):
        """Test disabled insert batching."""
        config = BatchConfig(batch_inserts=False)
        assert config.batch_inserts is False
    
    def test_no_return_results(self):
        """Test no return results."""
        config = BatchConfig(return_results=False)
        assert config.return_results is False


# =============================================================================
# BatchResult Tests
# =============================================================================

class TestBatchResult:
    """Tests for BatchResult dataclass."""
    
    def test_empty_result(self):
        """Test empty batch result."""
        result = BatchResult()
        assert result.total_rows == 0
        assert result.affected_rows == 0
        assert result.batches == 0
        assert result.success is True
    
    def test_success_with_errors(self):
        """Test success is False with errors."""
        result = BatchResult(errors=["Error 1"])
        assert result.success is False
    
    def test_rows_per_second(self):
        """Test rows per second calculation."""
        result = BatchResult(total_rows=1000, duration_ms=100.0)
        assert result.rows_per_second == 10000.0
    
    def test_rows_per_second_zero_duration(self):
        """Test rows per second with zero duration."""
        result = BatchResult(total_rows=1000, duration_ms=0)
        assert result.rows_per_second == 0.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        result = BatchResult(total_rows=100, affected_rows=95)
        d = result.to_dict()
        assert "total_rows" in d
        assert "affected_rows" in d
        assert "rows_per_second" in d


# =============================================================================
# BatchStats Tests
# =============================================================================

class TestBatchStats:
    """Tests for BatchStats dataclass."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = BatchStats()
        assert stats.total_operations == 0
        assert stats.total_rows == 0
        assert stats.inserts == 0
    
    def test_avg_batch_size(self):
        """Test average batch size calculation."""
        stats = BatchStats(total_rows=1000, total_batches=10)
        assert stats.avg_batch_size == 100.0
    
    def test_avg_duration(self):
        """Test average duration calculation."""
        stats = BatchStats(total_operations=10, total_duration_ms=1000.0)
        assert stats.avg_duration_ms == 100.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = BatchStats(inserts=5, updates=3)
        d = stats.to_dict()
        assert d["inserts"] == 5
        assert d["updates"] == 3


# =============================================================================
# BatchOptimizer Insert Tests
# =============================================================================

class TestBatchInsert:
    """Tests for batch insert operations."""
    
    @pytest.fixture
    def optimizer(self):
        async def executor(sql, params):
            return len(params) // 2  # Simulate affected rows
        return BatchOptimizer(executor=executor)
    
    @pytest.mark.asyncio
    async def test_insert_single_row(self, optimizer):
        """Test inserting a single row."""
        result = await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice", "email": "alice@example.com"}],
        )
        
        assert result.total_rows == 1
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_insert_multiple_rows(self, optimizer):
        """Test inserting multiple rows."""
        rows = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(10)
        ]
        
        result = await optimizer.insert_many(table="users", rows=rows)
        
        assert result.total_rows == 10
        assert result.batches >= 1
    
    @pytest.mark.asyncio
    async def test_insert_empty_rows(self, optimizer):
        """Test inserting empty rows list."""
        result = await optimizer.insert_many(table="users", rows=[])
        
        assert result.total_rows == 0
        assert result.batches == 0
    
    @pytest.mark.asyncio
    async def test_insert_with_columns(self, optimizer):
        """Test inserting with explicit columns."""
        rows = [{"name": "Alice", "email": "alice@example.com", "age": 30}]
        
        result = await optimizer.insert_many(
            table="users",
            rows=rows,
            columns=["name", "email"],  # Only these columns
        )
        
        assert result.total_rows == 1
    
    @pytest.mark.asyncio
    async def test_insert_batching(self):
        """Test rows are batched correctly."""
        batch_sizes = []
        
        async def tracking_executor(sql, params):
            # Count parameter placeholders
            batch_sizes.append(sql.count("$"))
            return 10
        
        optimizer = BatchOptimizer(
            config=BatchConfig(max_batch_size=5),
            executor=tracking_executor,
        )
        
        rows = [{"col": i} for i in range(12)]
        result = await optimizer.insert_many(table="test", rows=rows)
        
        assert result.batches == 3  # 5 + 5 + 2
    
    @pytest.mark.asyncio
    async def test_insert_stats_updated(self, optimizer):
        """Test insert updates statistics."""
        await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice"}],
        )
        
        stats = optimizer.get_stats()
        assert stats.inserts == 1
        assert stats.total_rows == 1


# =============================================================================
# BatchOptimizer Update Tests
# =============================================================================

class TestBatchUpdate:
    """Tests for batch update operations."""
    
    @pytest.fixture
    def optimizer(self):
        async def executor(sql, params):
            return 1
        return BatchOptimizer(executor=executor)
    
    @pytest.mark.asyncio
    async def test_update_single_row(self, optimizer):
        """Test updating a single row."""
        result = await optimizer.update_many(
            table="users",
            updates=[{"id": 1, "name": "Updated Name"}],
            set_columns=["name"],
            where_columns=["id"],
        )
        
        assert result.total_rows == 1
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_update_multiple_rows(self, optimizer):
        """Test updating multiple rows."""
        updates = [
            {"id": i, "name": f"Updated{i}"}
            for i in range(5)
        ]
        
        result = await optimizer.update_many(
            table="users",
            updates=updates,
            set_columns=["name"],
            where_columns=["id"],
        )
        
        assert result.total_rows == 5
    
    @pytest.mark.asyncio
    async def test_update_empty(self, optimizer):
        """Test updating empty list."""
        result = await optimizer.update_many(
            table="users",
            updates=[],
            set_columns=["name"],
            where_columns=["id"],
        )
        
        assert result.total_rows == 0
    
    @pytest.mark.asyncio
    async def test_update_stats_updated(self, optimizer):
        """Test update updates statistics."""
        await optimizer.update_many(
            table="users",
            updates=[{"id": 1, "name": "New"}],
            set_columns=["name"],
            where_columns=["id"],
        )
        
        stats = optimizer.get_stats()
        assert stats.updates == 1


# =============================================================================
# BatchOptimizer Upsert Tests
# =============================================================================

class TestBatchUpsert:
    """Tests for batch upsert operations."""
    
    @pytest.fixture
    def optimizer(self):
        async def executor(sql, params):
            return len(params) // 2
        return BatchOptimizer(executor=executor)
    
    @pytest.mark.asyncio
    async def test_upsert_single_row(self, optimizer):
        """Test upserting a single row."""
        result = await optimizer.upsert_many(
            table="users",
            rows=[{"email": "alice@example.com", "name": "Alice"}],
            conflict_columns=["email"],
            update_columns=["name"],
        )
        
        assert result.total_rows == 1
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_upsert_multiple_rows(self, optimizer):
        """Test upserting multiple rows."""
        rows = [
            {"email": f"user{i}@example.com", "name": f"User{i}"}
            for i in range(10)
        ]
        
        result = await optimizer.upsert_many(
            table="users",
            rows=rows,
            conflict_columns=["email"],
            update_columns=["name"],
        )
        
        assert result.total_rows == 10
    
    @pytest.mark.asyncio
    async def test_upsert_empty(self, optimizer):
        """Test upserting empty list."""
        result = await optimizer.upsert_many(
            table="users",
            rows=[],
            conflict_columns=["email"],
            update_columns=["name"],
        )
        
        assert result.total_rows == 0
    
    @pytest.mark.asyncio
    async def test_upsert_stats_updated(self, optimizer):
        """Test upsert updates statistics."""
        await optimizer.upsert_many(
            table="users",
            rows=[{"email": "a@b.com", "name": "Name"}],
            conflict_columns=["email"],
            update_columns=["name"],
        )
        
        stats = optimizer.get_stats()
        assert stats.upserts == 1


# =============================================================================
# BatchOptimizer Delete Tests
# =============================================================================

class TestBatchDelete:
    """Tests for batch delete operations."""
    
    @pytest.fixture
    def optimizer(self):
        async def executor(sql, params):
            return len(params)
        return BatchOptimizer(executor=executor)
    
    @pytest.mark.asyncio
    async def test_delete_by_ids(self, optimizer):
        """Test deleting by IDs."""
        result = await optimizer.delete_many(
            table="users",
            ids=[1, 2, 3],
        )
        
        assert result.total_rows == 3
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_delete_custom_column(self, optimizer):
        """Test deleting by custom ID column."""
        result = await optimizer.delete_many(
            table="users",
            ids=["alice@example.com", "bob@example.com"],
            id_column="email",
        )
        
        assert result.total_rows == 2
    
    @pytest.mark.asyncio
    async def test_delete_empty(self, optimizer):
        """Test deleting empty list."""
        result = await optimizer.delete_many(
            table="users",
            ids=[],
        )
        
        assert result.total_rows == 0


# =============================================================================
# Batch Size Limits Tests
# =============================================================================

class TestBatchSizeLimits:
    """Tests for batch size limits."""
    
    @pytest.mark.asyncio
    async def test_respects_max_batch_size(self):
        """Test batch respects max_batch_size."""
        batch_count = 0
        
        async def counting_executor(sql, params):
            nonlocal batch_count
            batch_count += 1
            return len(params)
        
        optimizer = BatchOptimizer(
            config=BatchConfig(max_batch_size=10),
            executor=counting_executor,
        )
        
        rows = [{"col": i} for i in range(25)]
        result = await optimizer.insert_many(table="test", rows=rows)
        
        assert result.batches == 3  # 10 + 10 + 5
        assert batch_count == 3
    
    @pytest.mark.asyncio
    async def test_respects_param_limit(self):
        """Test batch respects parameter limit."""
        optimizer = BatchOptimizer(
            config=BatchConfig(max_params=10, max_batch_size=1000),
            executor=AsyncMock(return_value=10),
        )
        
        # 5 columns per row, limit of 10 params = 2 rows per batch
        rows = [
            {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
            for _ in range(6)
        ]
        
        result = await optimizer.insert_many(table="test", rows=rows)
        
        assert result.batches == 3  # 2 + 2 + 2


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestBatchErrors:
    """Tests for batch error handling."""
    
    @pytest.mark.asyncio
    async def test_executor_error_captured(self):
        """Test executor error is captured in result."""
        async def failing_executor(sql, params):
            raise ValueError("Database error")
        
        optimizer = BatchOptimizer(executor=failing_executor)
        
        result = await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice"}],
        )
        
        assert result.success is False
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_partial_batch_failure(self):
        """Test partial batch failure."""
        call_count = 0
        
        async def sometimes_failing_executor(sql, params):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Second batch failed")
            return 5
        
        optimizer = BatchOptimizer(
            config=BatchConfig(max_batch_size=5),
            executor=sometimes_failing_executor,
        )
        
        rows = [{"col": i} for i in range(15)]
        result = await optimizer.insert_many(table="test", rows=rows)
        
        assert result.success is False
        assert len(result.errors) == 1
        assert result.affected_rows > 0  # First batch succeeded
    
    @pytest.mark.asyncio
    async def test_error_stats_updated(self):
        """Test error statistics are updated."""
        async def failing_executor(sql, params):
            raise ValueError("Failed")
        
        optimizer = BatchOptimizer(executor=failing_executor)
        
        await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice"}],
        )
        
        stats = optimizer.get_stats()
        assert stats.errors == 1


# =============================================================================
# SQL Generation Tests
# =============================================================================

class TestSQLGeneration:
    """Tests for SQL generation."""
    
    @pytest.mark.asyncio
    async def test_insert_sql_format(self):
        """Test insert SQL is correctly formatted."""
        captured_sql = None
        
        async def capturing_executor(sql, params):
            nonlocal captured_sql
            captured_sql = sql
            return 1
        
        optimizer = BatchOptimizer(executor=capturing_executor)
        
        await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice", "age": 30}],
        )
        
        assert "INSERT INTO users" in captured_sql
        assert "RETURNING *" in captured_sql
    
    @pytest.mark.asyncio
    async def test_insert_sql_no_returning(self):
        """Test insert SQL without RETURNING."""
        captured_sql = None
        
        async def capturing_executor(sql, params):
            nonlocal captured_sql
            captured_sql = sql
            return 1
        
        optimizer = BatchOptimizer(
            config=BatchConfig(return_results=False),
            executor=capturing_executor,
        )
        
        await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice"}],
        )
        
        assert "RETURNING" not in captured_sql
    
    @pytest.mark.asyncio
    async def test_upsert_sql_format(self):
        """Test upsert SQL is correctly formatted."""
        captured_sql = None
        
        async def capturing_executor(sql, params):
            nonlocal captured_sql
            captured_sql = sql
            return 1
        
        optimizer = BatchOptimizer(executor=capturing_executor)
        
        await optimizer.upsert_many(
            table="users",
            rows=[{"email": "a@b.com", "name": "Alice"}],
            conflict_columns=["email"],
            update_columns=["name"],
        )
        
        assert "ON CONFLICT" in captured_sql
        assert "email" in captured_sql
        assert "DO UPDATE SET" in captured_sql
        assert "EXCLUDED" in captured_sql


# =============================================================================
# Statistics Tests
# =============================================================================

class TestBatchStatistics:
    """Tests for batch statistics."""
    
    @pytest.mark.asyncio
    async def test_stats_after_operations(self):
        """Test statistics after operations."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=10))
        
        await optimizer.insert_many(table="t1", rows=[{"a": 1}])
        await optimizer.insert_many(table="t2", rows=[{"b": 2}])
        await optimizer.update_many(
            table="t1",
            updates=[{"id": 1, "a": 2}],
            set_columns=["a"],
            where_columns=["id"],
        )
        
        stats = optimizer.get_stats()
        assert stats.total_operations == 3
        assert stats.inserts == 2
        assert stats.updates == 1
    
    @pytest.mark.asyncio
    async def test_stats_reset(self):
        """Test statistics reset."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        await optimizer.insert_many(table="test", rows=[{"a": 1}])
        
        optimizer.reset_stats()
        stats = optimizer.get_stats()
        
        assert stats.total_operations == 0
        assert stats.inserts == 0


# =============================================================================
# Convenience Config Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_bulk_load_config(self):
        """Test bulk load configuration."""
        config = bulk_load_config()
        assert config.max_batch_size == 5000
        assert config.return_results is False
    
    def test_transactional_config(self):
        """Test transactional configuration."""
        config = transactional_config()
        assert config.max_batch_size == 100
        assert config.return_results is True
    
    def test_disabled_config(self):
        """Test disabled configuration."""
        config = disabled_batch_config()
        assert config.enabled is False


# =============================================================================
# Repr Tests
# =============================================================================

class TestBatchRepr:
    """Tests for batch optimizer string representation."""
    
    def test_repr(self):
        """Test optimizer repr."""
        optimizer = BatchOptimizer()
        repr_str = repr(optimizer)
        assert "BatchOptimizer" in repr_str


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestBatchEdgeCases:
    """Tests for batch edge cases."""
    
    @pytest.mark.asyncio
    async def test_none_values(self):
        """Test inserting None values."""
        captured_params = None
        
        async def capturing_executor(sql, params):
            nonlocal captured_params
            captured_params = params
            return 1
        
        optimizer = BatchOptimizer(executor=capturing_executor)
        
        await optimizer.insert_many(
            table="users",
            rows=[{"name": "Alice", "age": None}],
        )
        
        assert None in captured_params
    
    @pytest.mark.asyncio
    async def test_special_characters_in_values(self):
        """Test values with special characters."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        result = await optimizer.insert_many(
            table="users",
            rows=[{"name": "O'Brien", "email": "test@example.com"}],
        )
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_unicode_values(self):
        """Test Unicode values."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        result = await optimizer.insert_many(
            table="users",
            rows=[{"name": "日本語", "emoji": "🎉"}],
        )
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_single_column(self):
        """Test single column insert."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        result = await optimizer.insert_many(
            table="tags",
            rows=[{"name": "tag1"}, {"name": "tag2"}],
        )
        
        assert result.total_rows == 2
    
    @pytest.mark.asyncio
    async def test_many_columns(self):
        """Test many columns insert."""
        optimizer = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        row = {f"col{i}": i for i in range(50)}
        
        result = await optimizer.insert_many(
            table="wide_table",
            rows=[row],
        )
        
        assert result.success is True

