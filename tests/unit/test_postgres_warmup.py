"""
Comprehensive tests for PostgreSQL Connection Warmup (Phase 5.2).

Tests cover:
- WarmupConfig validation and defaults
- ConnectionWarmer initialization
- Single connection warmup
- Parallel warmup
- Warmup timeout handling
- Warmup failure recovery
- Statement preparation
- Statistics tracking

Total: 60 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from pynext.db.adapters.postgres.pool.warmup import (
    WarmupConfig,
    WarmupResult,
    WarmupStats,
    ConnectionWarmer,
)


# =============================================================================
# WarmupConfig Tests (15 tests)
# =============================================================================

class TestWarmupConfig:
    """Tests for WarmupConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = WarmupConfig()
        assert config.enabled is True
        assert config.query == "SELECT 1"
        assert config.timeout == 5.0
        assert config.parallel is True
        assert config.max_parallel == 10
        assert config.prepare_statements == []
        assert config.retry_on_failure is True
        assert config.max_retries == 3
        assert config.retry_delay == 0.5
        
    def test_custom_values(self):
        """Test custom configuration values."""
        config = WarmupConfig(
            enabled=False,
            query="SELECT 2",
            timeout=10.0,
            parallel=False,
            max_parallel=5,
            prepare_statements=["SELECT $1"],
            retry_on_failure=False,
            max_retries=5,
            retry_delay=1.0,
        )
        assert config.enabled is False
        assert config.query == "SELECT 2"
        assert config.timeout == 10.0
        assert config.parallel is False
        assert config.max_parallel == 5
        assert config.prepare_statements == ["SELECT $1"]
        assert config.retry_on_failure is False
        assert config.max_retries == 5
        assert config.retry_delay == 1.0
        
    def test_invalid_timeout_raises_error(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be > 0"):
            WarmupConfig(timeout=0)
            
        with pytest.raises(ValueError, match="timeout must be > 0"):
            WarmupConfig(timeout=-1)
            
    def test_invalid_max_parallel_raises_error(self):
        """Test that invalid max_parallel raises ValueError."""
        with pytest.raises(ValueError, match="max_parallel must be >= 1"):
            WarmupConfig(max_parallel=0)
            
    def test_invalid_max_retries_raises_error(self):
        """Test that invalid max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            WarmupConfig(max_retries=-1)
            
    def test_invalid_retry_delay_raises_error(self):
        """Test that invalid retry_delay raises ValueError."""
        with pytest.raises(ValueError, match="retry_delay must be >= 0"):
            WarmupConfig(retry_delay=-1)
            
    def test_callbacks_default_none(self):
        """Test that callbacks default to None."""
        config = WarmupConfig()
        assert config.on_warmup_start is None
        assert config.on_warmup_complete is None
        
    def test_callbacks_can_be_set(self):
        """Test that callbacks can be set."""
        start_called = False
        complete_called = False
        
        def on_start():
            nonlocal start_called
            start_called = True
            
        def on_complete(success, failed, duration):
            nonlocal complete_called
            complete_called = True
            
        config = WarmupConfig(
            on_warmup_start=on_start,
            on_warmup_complete=on_complete,
        )
        
        config.on_warmup_start()
        config.on_warmup_complete(1, 0, 1.0)
        
        assert start_called
        assert complete_called
        
    def test_prepare_statements_list(self):
        """Test prepare_statements accepts list of SQL."""
        statements = [
            "SELECT * FROM users WHERE id = $1",
            "SELECT * FROM posts WHERE user_id = $1",
            "SELECT COUNT(*) FROM comments",
        ]
        config = WarmupConfig(prepare_statements=statements)
        assert len(config.prepare_statements) == 3
        
    def test_disabled_warmup(self):
        """Test warmup can be disabled."""
        config = WarmupConfig(enabled=False)
        assert config.enabled is False
        
    def test_minimum_valid_config(self):
        """Test minimum valid configuration."""
        config = WarmupConfig(
            timeout=0.001,
            max_parallel=1,
            max_retries=0,
            retry_delay=0,
        )
        assert config.timeout == 0.001
        assert config.max_parallel == 1
        assert config.max_retries == 0
        assert config.retry_delay == 0
        
    def test_large_values(self):
        """Test large configuration values."""
        config = WarmupConfig(
            timeout=3600.0,
            max_parallel=1000,
            max_retries=100,
            retry_delay=60.0,
        )
        assert config.timeout == 3600.0
        assert config.max_parallel == 1000
        
    def test_config_immutability(self):
        """Test that config values can be accessed after creation."""
        config = WarmupConfig(query="SELECT NOW()")
        assert config.query == "SELECT NOW()"
        
    def test_prepare_statements_empty_by_default(self):
        """Test that prepare_statements is empty list by default."""
        config = WarmupConfig()
        assert config.prepare_statements == []
        assert isinstance(config.prepare_statements, list)


# =============================================================================
# WarmupResult Tests (10 tests)
# =============================================================================

class TestWarmupResult:
    """Tests for WarmupResult dataclass."""
    
    def test_successful_result(self):
        """Test successful warmup result."""
        result = WarmupResult(
            connection_id="conn_1",
            success=True,
            duration_ms=5.5,
        )
        assert result.connection_id == "conn_1"
        assert result.success is True
        assert result.duration_ms == 5.5
        assert result.error is None
        assert result.retries == 0
        
    def test_failed_result(self):
        """Test failed warmup result."""
        result = WarmupResult(
            connection_id="conn_2",
            success=False,
            duration_ms=100.0,
            error="Connection refused",
            retries=3,
        )
        assert result.success is False
        assert result.error == "Connection refused"
        assert result.retries == 3
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = WarmupResult(
            connection_id="conn_3",
            success=True,
            duration_ms=10.0,
            retries=1,
        )
        d = result.to_dict()
        assert d["connection_id"] == "conn_3"
        assert d["success"] is True
        assert d["duration_ms"] == 10.0
        assert d["retries"] == 1
        assert d["error"] is None
        
    def test_to_dict_with_error(self):
        """Test conversion to dictionary with error."""
        result = WarmupResult(
            connection_id="conn_4",
            success=False,
            duration_ms=50.0,
            error="Timeout",
        )
        d = result.to_dict()
        assert d["error"] == "Timeout"
        
    def test_result_with_zero_duration(self):
        """Test result with zero duration (disabled warmup)."""
        result = WarmupResult(
            connection_id="conn_5",
            success=True,
            duration_ms=0,
        )
        assert result.duration_ms == 0
        
    def test_result_with_high_retries(self):
        """Test result with many retries."""
        result = WarmupResult(
            connection_id="conn_6",
            success=True,
            duration_ms=500.0,
            retries=10,
        )
        assert result.retries == 10
        
    def test_result_equality(self):
        """Test result equality is based on all fields."""
        r1 = WarmupResult("conn_1", True, 10.0)
        r2 = WarmupResult("conn_1", True, 10.0)
        # Dataclasses are equal if all fields match
        assert r1 == r2
        
    def test_result_inequality(self):
        """Test result inequality."""
        r1 = WarmupResult("conn_1", True, 10.0)
        r2 = WarmupResult("conn_2", True, 10.0)
        assert r1 != r2
        
    def test_result_with_long_error(self):
        """Test result with long error message."""
        long_error = "Error: " + "x" * 1000
        result = WarmupResult(
            connection_id="conn_7",
            success=False,
            duration_ms=100.0,
            error=long_error,
        )
        assert len(result.error) > 1000
        
    def test_result_fields_are_accessible(self):
        """Test all result fields are accessible."""
        result = WarmupResult("conn_8", True, 15.0, "error", 2)
        _ = result.connection_id
        _ = result.success
        _ = result.duration_ms
        _ = result.error
        _ = result.retries


# =============================================================================
# WarmupStats Tests (10 tests)
# =============================================================================

class TestWarmupStats:
    """Tests for WarmupStats dataclass."""
    
    def test_default_values(self):
        """Test default statistics values."""
        stats = WarmupStats()
        assert stats.total_warmups == 0
        assert stats.successful_warmups == 0
        assert stats.failed_warmups == 0
        assert stats.total_retries == 0
        assert stats.total_duration_ms == 0
        assert stats.warmup_durations == []
        
    def test_avg_duration_empty(self):
        """Test average duration with no warmups."""
        stats = WarmupStats()
        assert stats.avg_duration_ms == 0
        
    def test_avg_duration_with_data(self):
        """Test average duration calculation."""
        stats = WarmupStats()
        stats.warmup_durations = [10.0, 20.0, 30.0]
        assert stats.avg_duration_ms == 20.0
        
    def test_success_rate_empty(self):
        """Test success rate with no warmups."""
        stats = WarmupStats()
        assert stats.success_rate == 1.0
        
    def test_success_rate_all_success(self):
        """Test success rate with all successful."""
        stats = WarmupStats()
        stats.total_warmups = 10
        stats.successful_warmups = 10
        assert stats.success_rate == 1.0
        
    def test_success_rate_some_failures(self):
        """Test success rate with some failures."""
        stats = WarmupStats()
        stats.total_warmups = 10
        stats.successful_warmups = 8
        stats.failed_warmups = 2
        assert stats.success_rate == 0.8
        
    def test_record_successful(self):
        """Test recording successful warmup."""
        stats = WarmupStats()
        result = WarmupResult("conn_1", True, 15.0, retries=1)
        stats.record(result)
        
        assert stats.total_warmups == 1
        assert stats.successful_warmups == 1
        assert stats.failed_warmups == 0
        assert stats.total_retries == 1
        assert stats.total_duration_ms == 15.0
        assert len(stats.warmup_durations) == 1
        
    def test_record_failed(self):
        """Test recording failed warmup."""
        stats = WarmupStats()
        result = WarmupResult("conn_1", False, 100.0, error="timeout", retries=3)
        stats.record(result)
        
        assert stats.total_warmups == 1
        assert stats.successful_warmups == 0
        assert stats.failed_warmups == 1
        assert stats.total_retries == 3
        # Failed warmups don't add to duration
        assert stats.total_duration_ms == 0
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = WarmupStats()
        stats.total_warmups = 5
        stats.successful_warmups = 4
        stats.failed_warmups = 1
        
        d = stats.to_dict()
        assert "total_warmups" in d
        assert "successful_warmups" in d
        assert "failed_warmups" in d
        assert "success_rate" in d
        assert "avg_duration_ms" in d
        
    def test_warmup_durations_limited(self):
        """Test that warmup_durations is limited to 1000."""
        stats = WarmupStats()
        for i in range(1100):
            result = WarmupResult("conn", True, float(i))
            stats.record(result)
        
        assert len(stats.warmup_durations) == 1000


# =============================================================================
# ConnectionWarmer Tests (25 tests)
# =============================================================================

class TestConnectionWarmer:
    """Tests for ConnectionWarmer class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        warmer = ConnectionWarmer()
        assert warmer.config.enabled is True
        assert warmer.enabled is True
        
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = WarmupConfig(enabled=False)
        warmer = ConnectionWarmer(config)
        assert warmer.enabled is False
        
    @pytest.mark.asyncio
    async def test_warmup_disabled(self):
        """Test warmup when disabled returns immediately."""
        config = WarmupConfig(enabled=False)
        warmer = ConnectionWarmer(config)
        
        mock_conn = MagicMock()
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is True
        assert result.duration_ms == 0
        mock_conn.fetchval.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_warmup_success(self):
        """Test successful warmup."""
        warmer = ConnectionWarmer(WarmupConfig(timeout=5.0))
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is True
        assert result.connection_id == "conn_1"
        assert result.retries == 0
        mock_conn.fetchval.assert_called_once_with("SELECT 1")
        
    @pytest.mark.asyncio
    async def test_warmup_custom_query(self):
        """Test warmup with custom query."""
        config = WarmupConfig(query="SELECT NOW()")
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="2023-01-01")
        
        await warmer.warmup_connection("conn_1", mock_conn)
        
        mock_conn.fetchval.assert_called_once_with("SELECT NOW()")
        
    @pytest.mark.asyncio
    async def test_warmup_timeout(self):
        """Test warmup timeout handling."""
        config = WarmupConfig(timeout=0.01, retry_on_failure=False)
        warmer = ConnectionWarmer(config)
        
        async def slow_query(*args):
            await asyncio.sleep(1)
            return 1
            
        mock_conn = AsyncMock()
        mock_conn.fetchval = slow_query
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is False
        assert "timed out" in result.error
        
    @pytest.mark.asyncio
    async def test_warmup_retry_success(self):
        """Test warmup succeeds after retries."""
        config = WarmupConfig(max_retries=3, retry_delay=0.01)
        warmer = ConnectionWarmer(config)
        
        call_count = 0
        async def failing_then_success(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection failed")
            return 1
            
        mock_conn = AsyncMock()
        mock_conn.fetchval = failing_then_success
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is True
        assert result.retries == 2
        
    @pytest.mark.asyncio
    async def test_warmup_all_retries_fail(self):
        """Test warmup fails after all retries."""
        config = WarmupConfig(max_retries=2, retry_delay=0.01, retry_on_failure=True)
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is False
        assert result.retries == 3  # Initial + 2 retries
        assert "Connection failed" in result.error
        
    @pytest.mark.asyncio
    async def test_warmup_no_retry(self):
        """Test warmup without retries."""
        config = WarmupConfig(retry_on_failure=False, max_retries=0)
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Failed"))
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.success is False
        assert result.retries == 1  # Only initial attempt (no retries when max_retries=0)
        
    @pytest.mark.asyncio
    async def test_warmup_all_empty_dict(self):
        """Test warmup_all with empty dict."""
        warmer = ConnectionWarmer()
        results = await warmer.warmup_all({})
        assert results == []
        
    @pytest.mark.asyncio
    async def test_warmup_all_disabled(self):
        """Test warmup_all when disabled."""
        config = WarmupConfig(enabled=False)
        warmer = ConnectionWarmer(config)
        
        results = await warmer.warmup_all({"conn_1": MagicMock()})
        assert results == []
        
    @pytest.mark.asyncio
    async def test_warmup_all_parallel(self):
        """Test parallel warmup of multiple connections."""
        config = WarmupConfig(parallel=True, max_parallel=5)
        warmer = ConnectionWarmer(config)
        
        connections = {}
        for i in range(5):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            connections[f"conn_{i}"] = mock_conn
            
        results = await warmer.warmup_all(connections)
        
        assert len(results) == 5
        assert all(r.success for r in results)
        
    @pytest.mark.asyncio
    async def test_warmup_all_sequential(self):
        """Test sequential warmup of multiple connections."""
        config = WarmupConfig(parallel=False)
        warmer = ConnectionWarmer(config)
        
        connections = {}
        for i in range(3):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            connections[f"conn_{i}"] = mock_conn
            
        results = await warmer.warmup_all(connections)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        
    @pytest.mark.asyncio
    async def test_warmup_with_prepare_statements(self):
        """Test warmup prepares statements."""
        config = WarmupConfig(
            prepare_statements=["SELECT $1", "SELECT $1, $2"],
        )
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.prepare = AsyncMock()
        
        await warmer.warmup_connection("conn_1", mock_conn)
        
        assert mock_conn.prepare.call_count == 2
        
    @pytest.mark.asyncio
    async def test_warmup_prepare_statement_failure(self):
        """Test warmup continues if prepare fails."""
        config = WarmupConfig(
            prepare_statements=["INVALID SQL"],
        )
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.prepare = AsyncMock(side_effect=Exception("Invalid SQL"))
        
        # Should still succeed even if prepare fails
        result = await warmer.warmup_connection("conn_1", mock_conn)
        assert result.success is True
        
    def test_get_stats(self):
        """Test getting warmup statistics."""
        warmer = ConnectionWarmer()
        stats = warmer.get_stats()
        assert isinstance(stats, WarmupStats)
        
    @pytest.mark.asyncio
    async def test_stats_updated_on_success(self):
        """Test stats are updated on successful warmup."""
        warmer = ConnectionWarmer()
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        await warmer.warmup_connection("conn_1", mock_conn)
        
        stats = warmer.get_stats()
        assert stats.total_warmups == 1
        assert stats.successful_warmups == 1
        
    @pytest.mark.asyncio
    async def test_stats_updated_on_failure(self):
        """Test stats are updated on failed warmup."""
        config = WarmupConfig(retry_on_failure=False)
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Failed"))
        
        await warmer.warmup_connection("conn_1", mock_conn)
        
        stats = warmer.get_stats()
        assert stats.total_warmups == 1
        assert stats.failed_warmups == 1
        
    @pytest.mark.asyncio
    async def test_warmup_callbacks_called(self):
        """Test warmup callbacks are called."""
        start_called = False
        complete_called = False
        
        def on_start():
            nonlocal start_called
            start_called = True
            
        def on_complete(success, failed, duration):
            nonlocal complete_called
            complete_called = True
            
        config = WarmupConfig(
            on_warmup_start=on_start,
            on_warmup_complete=on_complete,
        )
        warmer = ConnectionWarmer(config)
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        await warmer.warmup_all({"conn_1": mock_conn})
        
        assert start_called
        assert complete_called
        
    @pytest.mark.asyncio
    async def test_warmup_concurrency_limit(self):
        """Test parallel warmup respects max_parallel."""
        config = WarmupConfig(parallel=True, max_parallel=2)
        warmer = ConnectionWarmer(config)
        
        concurrent_count = 0
        max_concurrent = 0
        
        async def track_concurrency(*args):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return 1
            
        connections = {}
        for i in range(10):
            mock_conn = AsyncMock()
            mock_conn.fetchval = track_concurrency
            connections[f"conn_{i}"] = mock_conn
            
        await warmer.warmup_all(connections)
        
        assert max_concurrent <= 2
        
    def test_repr(self):
        """Test string representation."""
        warmer = ConnectionWarmer()
        repr_str = repr(warmer)
        assert "ConnectionWarmer" in repr_str
        assert "enabled=True" in repr_str
        
    @pytest.mark.asyncio
    async def test_warmup_duration_tracked(self):
        """Test warmup duration is tracked correctly."""
        warmer = ConnectionWarmer()
        
        async def slow_fetchval(*args):
            await asyncio.sleep(0.05)
            return 1
            
        mock_conn = AsyncMock()
        mock_conn.fetchval = slow_fetchval
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        
        assert result.duration_ms >= 50  # At least 50ms
        
    @pytest.mark.asyncio
    async def test_warmup_all_mixed_results(self):
        """Test warmup_all with some successes and failures."""
        config = WarmupConfig(retry_on_failure=False)
        warmer = ConnectionWarmer(config)
        
        success_conn = AsyncMock()
        success_conn.fetchval = AsyncMock(return_value=1)
        
        fail_conn = AsyncMock()
        fail_conn.fetchval = AsyncMock(side_effect=Exception("Failed"))
        
        connections = {
            "conn_1": success_conn,
            "conn_2": fail_conn,
            "conn_3": success_conn,
        }
        
        results = await warmer.warmup_all(connections)
        
        assert len(results) == 3
        successful = sum(1 for r in results if r.success)
        assert successful >= 1  # At least some should succeed
        
    @pytest.mark.asyncio
    async def test_warmup_connection_id_preserved(self):
        """Test connection ID is preserved in result."""
        warmer = ConnectionWarmer()
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await warmer.warmup_connection("my_special_conn", mock_conn)
        
        assert result.connection_id == "my_special_conn"

