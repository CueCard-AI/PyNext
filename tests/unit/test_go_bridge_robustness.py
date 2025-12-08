"""
Robustness tests for Go Bridge.

Tests edge cases, error handling, and boundary conditions
to ensure the Go bridge is bulletproof.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from pynext_go import GoBridge, GO_AVAILABLE
from pynext_go.config import BridgeConfig
from pynext_go.errors import (
    BridgeError,
    BridgeConfigError,
    BridgeConnectionError,
    BridgeQueryError,
    BridgeTimeoutError,
    BridgePoolError,
    BridgeArrowError,
    error_from_code,
)
from pynext_go.result import QueryResult
from pynext_go.health import HealthStatus, ConnectionHealth, PoolHealth


# =============================================================================
# Config Edge Cases
# =============================================================================

class TestConfigEdgeCases:
    """Test config validation edge cases."""
    
    def test_empty_primary_raises(self):
        """Empty primary should raise ValueError."""
        with pytest.raises(ValueError, match="required"):
            BridgeConfig(primary="")
    
    def test_non_postgres_dsn_raises(self):
        """Non-PostgreSQL DSN should raise ValueError."""
        with pytest.raises(ValueError, match="PostgreSQL"):
            BridgeConfig(primary="mysql://localhost/test")
    
    def test_pool_min_negative_raises(self):
        """Negative pool_min_size should raise ValueError."""
        with pytest.raises(ValueError):
            BridgeConfig(primary="postgresql://localhost/test", pool_min_size=-1)
    
    def test_pool_max_zero_raises(self):
        """Zero pool_max_size should raise ValueError."""
        with pytest.raises(ValueError):
            BridgeConfig(primary="postgresql://localhost/test", pool_max_size=0)
    
    def test_pool_min_greater_than_max_raises(self):
        """pool_min_size > pool_max_size should raise ValueError."""
        with pytest.raises(ValueError):
            BridgeConfig(primary="postgresql://localhost/test", pool_min_size=20, pool_max_size=10)
    
    def test_pool_min_equal_to_max_ok(self):
        """pool_min_size == pool_max_size should be valid."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=10,
            pool_max_size=10,
        )
        assert config.pool_min_size == 10
        assert config.pool_max_size == 10
    
    def test_timeout_negative_raises(self):
        """Negative timeout should raise ValueError."""
        with pytest.raises(ValueError):
            BridgeConfig(primary="postgresql://localhost/test", query_timeout=-1)
    
    def test_timeout_zero_ok(self):
        """Zero timeout (no timeout) should be valid."""
        config = BridgeConfig(primary="postgresql://localhost/test", query_timeout=0)
        assert config.query_timeout == 0
    
    def test_very_large_pool_size(self):
        """Very large pool sizes should be accepted."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_max_size=10000,
        )
        assert config.pool_max_size == 10000
    
    def test_dsn_with_special_chars(self):
        """DSN with special characters should be accepted."""
        dsn = "postgresql://user:p%40ss@localhost:5432/db?sslmode=require"
        config = BridgeConfig(primary=dsn)
        assert config.primary == dsn
    
    def test_replica_dsns_empty_list(self):
        """Empty replicas list should be valid."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            replicas=[],
        )
        assert config.replicas == []
    
    def test_replica_dsns_with_values(self):
        """Multiple replicas should be stored correctly."""
        replicas = [
            "postgresql://replica1/test",
            "postgresql://replica2/test",
        ]
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            replicas=replicas,
        )
        assert config.replicas == replicas


# =============================================================================
# Config Serialization
# =============================================================================

class TestConfigSerialization:
    """Test config JSON serialization edge cases."""
    
    def test_to_json_valid(self):
        """to_json should produce valid JSON."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        json_str = config.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "primary" in parsed
    
    def test_from_json_roundtrip(self):
        """Config should survive JSON roundtrip."""
        original = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=5,
            pool_max_size=25,
            query_timeout=15000,
        )
        
        json_str = original.to_json()
        restored = BridgeConfig.from_json(json_str)
        
        assert restored.primary == original.primary
        assert restored.pool_min_size == original.pool_min_size
        assert restored.pool_max_size == original.pool_max_size
        assert restored.query_timeout == original.query_timeout
    
    def test_from_json_invalid(self):
        """from_json with invalid JSON should raise."""
        with pytest.raises(json.JSONDecodeError):
            BridgeConfig.from_json("not valid json")
    
    def test_to_dict_contains_all_fields(self):
        """to_dict should include all config fields."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        d = config.to_dict()
        
        assert "primary" in d
        assert "replicas" in d
        assert "pool_min_size" in d
        assert "pool_max_size" in d
        assert "query_timeout" in d


# =============================================================================
# Error Handling
# =============================================================================

class TestErrorFromCode:
    """Test error_from_code factory function."""
    
    def test_code_0_generic_error(self):
        """Code 0 should produce BridgeError."""
        err = error_from_code(0, "test")
        assert isinstance(err, BridgeError)
    
    def test_code_1_config_error(self):
        """Code 1 should produce BridgeConfigError."""
        err = error_from_code(1, "test")
        assert isinstance(err, BridgeConfigError)
    
    def test_code_2_connection_error(self):
        """Code 2 should produce BridgeConnectionError."""
        err = error_from_code(2, "test")
        assert isinstance(err, BridgeConnectionError)
    
    def test_code_3_query_error(self):
        """Code 3 should produce BridgeQueryError."""
        err = error_from_code(3, "test")
        assert isinstance(err, BridgeQueryError)
    
    def test_code_4_timeout_error(self):
        """Code 4 should produce BridgeTimeoutError."""
        err = error_from_code(4, "test")
        assert isinstance(err, BridgeTimeoutError)
    
    def test_code_5_pool_error(self):
        """Code 5 should produce BridgePoolError."""
        err = error_from_code(5, "test")
        assert isinstance(err, BridgePoolError)
    
    def test_code_6_arrow_error(self):
        """Code 6 should produce BridgeArrowError."""
        err = error_from_code(6, "test")
        assert isinstance(err, BridgeArrowError)
    
    def test_unknown_code_generic_error(self):
        """Unknown codes should produce BridgeError."""
        err = error_from_code(999, "test")
        assert isinstance(err, BridgeError)
    
    def test_error_preserves_message(self):
        """Error message should be preserved."""
        msg = "Custom error message"
        err = error_from_code(3, msg)
        assert msg in str(err)


# =============================================================================
# BridgeError
# =============================================================================

class TestBridgeErrorStr:
    """Test BridgeError string representations."""
    
    def test_str_message_only(self):
        """str() with just message."""
        err = BridgeError("test message")
        assert str(err) == "test message"
    
    def test_error_is_exception(self):
        """BridgeError should be raiseable."""
        with pytest.raises(BridgeError):
            raise BridgeError("test")
    
    def test_error_inheritance(self):
        """All errors should inherit from BridgeError."""
        assert issubclass(BridgeConfigError, BridgeError)
        assert issubclass(BridgeConnectionError, BridgeError)
        assert issubclass(BridgeQueryError, BridgeError)
        assert issubclass(BridgeTimeoutError, BridgeError)
        assert issubclass(BridgePoolError, BridgeError)
        assert issubclass(BridgeArrowError, BridgeError)


# =============================================================================
# QueryResult Edge Cases
# =============================================================================

class TestQueryResultEdgeCases:
    """Extended edge case tests for QueryResult."""
    
    def test_empty_result(self):
        """Empty result should have correct properties."""
        result = QueryResult(
            success=True,
            rows=[],
            columns=[],
            rows_affected=0,
        )
        
        assert result.success
        assert result.is_empty
        assert len(result) == 0
        assert result.first() is None
        assert result.first_dict() is None
    
    def test_single_row(self):
        """Single row result."""
        result = QueryResult(
            success=True,
            rows=[[1, "test"]],
            columns=["id", "name"],
            rows_affected=1,
        )
        
        assert not result.is_empty
        assert len(result) == 1
        assert result.first() == [1, "test"]
        assert result.first_dict() == {"id": 1, "name": "test"}
    
    def test_one_raises_on_empty(self):
        """one() should raise on empty result."""
        result = QueryResult(success=True, rows=[], columns=[])
        
        with pytest.raises(ValueError, match="none"):
            result.one()
    
    def test_one_raises_on_multiple(self):
        """one() should raise on multiple rows."""
        result = QueryResult(
            success=True,
            rows=[[1], [2]],
            columns=["id"],
        )
        
        with pytest.raises(ValueError, match="got 2"):
            result.one()
    
    def test_one_succeeds_on_single(self):
        """one() should succeed on exactly one row."""
        result = QueryResult(
            success=True,
            rows=[[42]],
            columns=["id"],
        )
        
        assert result.one() == [42]
    
    def test_scalar_single_column_single_row(self):
        """scalar() on single column, single row."""
        result = QueryResult(
            success=True,
            rows=[[42]],
            columns=["count"],
        )
        
        assert result.scalar() == 42
    
    def test_scalar_raises_on_empty(self):
        """scalar() should raise on empty result."""
        result = QueryResult(success=True, rows=[], columns=["id"])
        
        with pytest.raises(ValueError):
            result.scalar()
    
    def test_iteration(self):
        """Results should be iterable."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"], [3, "c"]],
            columns=["id", "name"],
        )
        
        rows = list(result)
        assert len(rows) == 3
        assert rows[0] == [1, "a"]
    
    def test_indexing(self):
        """Results should support indexing."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"], [3, "c"]],
            columns=["id", "name"],
        )
        
        assert result[0] == [1, "a"]
        assert result[2] == [3, "c"]
    
    def test_negative_indexing(self):
        """Results should support negative indexing."""
        result = QueryResult(
            success=True,
            rows=[[1], [2], [3]],
            columns=["id"],
        )
        
        assert result[-1] == [3]
    
    def test_index_out_of_range(self):
        """Out of range index should raise IndexError."""
        result = QueryResult(
            success=True,
            rows=[[1]],
            columns=["id"],
        )
        
        with pytest.raises(IndexError):
            _ = result[10]
    
    def test_column_by_name(self):
        """column() by name should work."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"]],
            columns=["id", "name"],
        )
        
        names = result.column("name")
        assert names == ["a", "b"]
    
    def test_column_not_found(self):
        """column() with invalid name should raise KeyError."""
        result = QueryResult(
            success=True,
            rows=[[1]],
            columns=["id"],
        )
        
        with pytest.raises(KeyError):
            result.column("invalid")
    
    def test_to_dicts(self):
        """to_dicts should return list of dicts."""
        result = QueryResult(
            success=True,
            rows=[[1, "a"], [2, "b"]],
            columns=["id", "name"],
        )
        
        dicts = result.to_dicts()
        assert dicts == [
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
        ]
    
    def test_failed_result(self):
        """Failed result should have success=False."""
        result = QueryResult(
            success=False,
            error="connection failed",
        )
        
        assert not result.success
        assert "connection" in result.error


# =============================================================================
# Health Status Edge Cases
# =============================================================================

class TestHealthStatusEdgeCases:
    """Test HealthStatus edge cases."""
    
    def test_healthy_status(self):
        """Healthy status should have is_healthy=True."""
        health = HealthStatus(
            status="healthy",
            primary=ConnectionHealth(url="***", status="ok", latency_ms=1.0),
            replicas=[],
            pool=PoolHealth(total_conns=10, idle_conns=5, active_conns=5),
            timestamp=datetime.now(),
        )
        assert health.is_healthy
        assert not health.is_unhealthy
    
    def test_unhealthy_status(self):
        """Unhealthy status should have is_unhealthy=True."""
        health = HealthStatus(
            status="unhealthy",
            primary=ConnectionHealth(url="***", status="down", latency_ms=0.0, error="refused"),
            replicas=[],
            pool=PoolHealth(total_conns=0, idle_conns=0, active_conns=0),
            timestamp=datetime.now(),
        )
        assert health.is_unhealthy
        assert not health.is_healthy
    
    def test_degraded_status(self):
        """Degraded status."""
        health = HealthStatus(
            status="degraded",
            primary=ConnectionHealth(url="***", status="degraded", latency_ms=150.0),
            replicas=[],
            pool=PoolHealth(total_conns=10, idle_conns=1, active_conns=9),
            timestamp=datetime.now(),
        )
        assert health.is_degraded
    
    def test_from_dict(self):
        """from_dict should work with full data."""
        data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "primary": {
                "url": "***",
                "status": "ok",
                "latency_ms": 1.5,
            },
            "pool": {
                "total_conns": 10,
                "idle_conns": 5,
                "active_conns": 5,
            },
        }
        
        health = HealthStatus.from_dict(data)
        assert health.status == "healthy"
    
    def test_summary(self):
        """summary() should produce readable output."""
        health = HealthStatus(
            status="healthy",
            primary=ConnectionHealth(url="***", status="ok", latency_ms=1.0),
            replicas=[],
            pool=PoolHealth(total_conns=10, idle_conns=5, active_conns=5),
            timestamp=datetime.now(),
        )
        
        summary = health.summary()
        assert "healthy" in summary.lower()


# =============================================================================
# Connection Health
# =============================================================================

class TestConnectionHealth:
    """Test ConnectionHealth."""
    
    def test_ok_status(self):
        """OK status properties."""
        conn = ConnectionHealth(url="***", status="ok", latency_ms=1.0)
        assert conn.is_ok
        assert not conn.is_down
    
    def test_down_status(self):
        """Down status properties."""
        conn = ConnectionHealth(url="***", status="down", latency_ms=0.0, error="refused")
        assert conn.is_down
        assert not conn.is_ok
    
    def test_degraded_status(self):
        """Degraded status properties."""
        conn = ConnectionHealth(url="***", status="degraded", latency_ms=150.0)
        assert conn.is_degraded
        assert not conn.is_ok


# =============================================================================
# Pool Health
# =============================================================================

class TestPoolHealth:
    """Test PoolHealth."""
    
    def test_utilization_calculation(self):
        """Utilization should be calculated correctly."""
        pool = PoolHealth(
            total_conns=10,
            idle_conns=2,
            active_conns=8,
        )
        # Returns as percentage (0-100)
        assert pool.utilization == 80.0
    
    def test_utilization_zero_total(self):
        """Utilization with zero total should be 0."""
        pool = PoolHealth(total_conns=0, idle_conns=0, active_conns=0)
        assert pool.utilization == 0.0
    
    def test_is_exhausted(self):
        """is_exhausted when idle=0 and waiting>0."""
        pool = PoolHealth(
            total_conns=10,
            idle_conns=0,
            active_conns=10,
            waiting_reqs=5,  # Some requests waiting
        )
        assert pool.is_exhausted
    
    def test_not_exhausted(self):
        """Not exhausted when idle connections exist."""
        pool = PoolHealth(
            total_conns=10,
            idle_conns=5,
            active_conns=5,
            waiting_reqs=0,
        )
        assert not pool.is_exhausted


# =============================================================================
# GoBridge Edge Cases
# =============================================================================

class TestGoBridgeEdgeCases:
    """Extended edge case tests for GoBridge."""
    
    def test_version_is_string(self):
        """version() should return a string."""
        version = GoBridge.version()
        assert isinstance(version, str)
    
    def test_is_available_is_bool(self):
        """is_available should be boolean."""
        bridge = GoBridge()
        assert isinstance(bridge.is_available, bool)
    
    def test_is_initialized_false_initially(self):
        """is_initialized should be False before init."""
        bridge = GoBridge()
        assert not bridge.is_initialized
    
    def test_config_none_before_init(self):
        """config should be None before init."""
        bridge = GoBridge()
        assert bridge.config is None
    
    def test_close_safe_without_init(self):
        """close() should be safe without init."""
        bridge = GoBridge()
        bridge.close()  # Should not raise
    
    def test_close_idempotent(self):
        """close() should be idempotent."""
        bridge = GoBridge()
        bridge.close()
        bridge.close()
        bridge.close()  # Should not raise
    
    def test_execute_raises_not_initialized(self):
        """execute() without init should raise."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            bridge.execute("SELECT 1")
    
    def test_execute_batch_raises_not_initialized(self):
        """execute_batch() without init should raise."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            bridge.execute_batch([("SELECT 1", [])])
    
    def test_health_raises_not_initialized(self):
        """health() without init should raise."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            bridge.health()
    
    def test_warmup_raises_not_initialized(self):
        """warmup() without init should raise."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            bridge.warmup()


# =============================================================================
# Memory Safety
# =============================================================================

class TestMemorySafety:
    """Test memory safety considerations."""
    
    def test_large_result_handling(self):
        """Large results should not cause issues."""
        # Simulate large result
        rows = [[i, f"name_{i}"] for i in range(10000)]
        columns = ["id", "name"]
        
        result = QueryResult(
            success=True,
            rows=rows,
            columns=columns,
        )
        
        assert len(result) == 10000
        
        # Iteration should work
        count = 0
        for _ in result:
            count += 1
        assert count == 10000
    
    def test_empty_string_values(self):
        """Empty strings should be handled correctly."""
        result = QueryResult(
            success=True,
            rows=[["", ""]],
            columns=["a", "b"],
        )
        
        row = result.first_dict()
        assert row["a"] == ""
        assert row["b"] == ""
    
    def test_null_values(self):
        """NULL values should be handled correctly."""
        result = QueryResult(
            success=True,
            rows=[[None, None]],
            columns=["a", "b"],
        )
        
        row = result.first_dict()
        assert row["a"] is None
        assert row["b"] is None
    
    def test_special_characters_in_strings(self):
        """Special characters should be preserved."""
        special = "Hello\nWorld\t👋"
        result = QueryResult(
            success=True,
            rows=[[special]],
            columns=["msg"],
        )
        
        row = result.first_dict()
        assert "Hello" in row["msg"]
        assert "World" in row["msg"]
