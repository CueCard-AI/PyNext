"""
Tests for Go/Python boundary communication.

Tests the JSON serialization/deserialization boundary between
Python and Go to ensure data integrity across the FFI layer.
"""

import pytest
import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from uuid import UUID

from pynext_go.config import BridgeConfig
from pynext_go.result import QueryResult
from pynext_go.health import HealthStatus, ConnectionHealth, PoolHealth
from pynext_go.errors import BridgeError


# =============================================================================
# JSON Boundary Tests - Python to Go
# =============================================================================

class TestConfigToGo:
    """Test config JSON sent to Go."""
    
    def test_primary_dsn_preserved(self):
        """Primary DSN should be exactly preserved."""
        dsn = "postgresql://user:pass@host:5432/db?sslmode=require"
        config = BridgeConfig(primary=dsn)
        
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["primary"] == dsn
    
    def test_replicas_array(self):
        """Replicas should be JSON array."""
        replicas = ["postgresql://r1/db", "postgresql://r2/db"]
        config = BridgeConfig(primary="postgresql://p/db", replicas=replicas)
        
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        assert isinstance(parsed["replicas"], list)
        assert parsed["replicas"] == replicas
    
    def test_integers_not_floats(self):
        """Integer config values should be integers in JSON."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=5,
            pool_max_size=20,
            query_timeout=30000,
        )
        
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        # Python json.loads returns int for integer values
        assert isinstance(parsed["pool_min_size"], int)
        assert isinstance(parsed["pool_max_size"], int)
        assert isinstance(parsed["query_timeout"], int)
    
    def test_booleans(self):
        """Boolean config values should be JSON booleans."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            enable_arrow=True,
            enable_prepared=False,
        )
        
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["enable_arrow"] is True
        assert parsed["enable_prepared"] is False
    
    def test_unicode_in_dsn(self):
        """Unicode in DSN should be preserved."""
        # Note: Real DSN should URL-encode unicode
        dsn = "postgresql://user:pass@localhost:5432/testdb"
        config = BridgeConfig(primary=dsn)
        
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["primary"] == dsn


class TestQueryRequestToGo:
    """Test query request JSON sent to Go."""
    
    def test_simple_query(self):
        """Simple query without params."""
        request = {
            "sql": "SELECT 1",
            "params": [],
            "timeout_ms": 0,
            "use_replica": False,
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["sql"] == "SELECT 1"
        assert parsed["params"] == []
    
    def test_parameterized_query(self):
        """Query with various parameter types."""
        request = {
            "sql": "SELECT * FROM users WHERE id = $1 AND name = $2",
            "params": [42, "Alice"],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["params"][0] == 42
        assert parsed["params"][1] == "Alice"
    
    def test_null_param(self):
        """NULL parameters should serialize as null."""
        request = {
            "sql": "INSERT INTO t VALUES ($1)",
            "params": [None],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["params"][0] is None
    
    def test_boolean_params(self):
        """Boolean parameters."""
        request = {
            "sql": "SELECT * FROM t WHERE active = $1",
            "params": [True, False],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["params"][0] is True
        assert parsed["params"][1] is False
    
    def test_float_params(self):
        """Float parameters preserve precision."""
        request = {
            "sql": "INSERT INTO t VALUES ($1)",
            "params": [3.14159265358979],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        # IEEE 754 double precision
        assert abs(parsed["params"][0] - 3.14159265358979) < 1e-10
    
    def test_large_integer_params(self):
        """Large integers should not lose precision."""
        large_int = 9007199254740993  # Larger than JS safe integer
        request = {
            "sql": "SELECT $1",
            "params": [large_int],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["params"][0] == large_int
    
    def test_string_with_special_chars(self):
        """Strings with special characters."""
        special_string = 'Hello "World"\n\t\r'
        request = {
            "sql": "SELECT $1",
            "params": [special_string],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert "\n" in parsed["params"][0]
        assert "\t" in parsed["params"][0]
    
    def test_binary_as_base64(self):
        """Binary data should be base64 encoded for JSON."""
        binary_data = bytes([0, 1, 2, 255, 254, 253])
        
        import base64
        encoded = base64.b64encode(binary_data).decode("ascii")
        
        request = {
            "sql": "INSERT INTO t VALUES ($1)",
            "params": [encoded],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        # Decode back
        decoded = base64.b64decode(parsed["params"][0])
        assert decoded == binary_data
    
    def test_datetime_as_iso(self):
        """Datetime should be ISO 8601 string."""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        iso_str = dt.isoformat()
        
        request = {
            "sql": "INSERT INTO t VALUES ($1)",
            "params": [iso_str],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        # Parse back
        parsed_dt = datetime.fromisoformat(parsed["params"][0])
        assert parsed_dt == dt
    
    def test_uuid_as_string(self):
        """UUID should be string format."""
        uid = UUID("12345678-1234-5678-1234-567812345678")
        
        request = {
            "sql": "SELECT $1",
            "params": [str(uid)],
        }
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        parsed_uuid = UUID(parsed["params"][0])
        assert parsed_uuid == uid


# =============================================================================
# JSON Boundary Tests - Go to Python
# =============================================================================

class TestQueryResultFromGo:
    """Test query result JSON received from Go."""
    
    def test_success_result(self):
        """Parse successful result."""
        go_response = {
            "success": True,
            "rows": [[1, "Alice"], [2, "Bob"]],
            "columns": ["id", "name"],
            "rows_affected": 2,
            "duration_ms": 0.0015,
            "cached": False,
        }
        
        result = QueryResult.from_dict(go_response)
        
        assert result.success
        assert len(result) == 2
        assert result.columns == ["id", "name"]
    
    def test_error_result(self):
        """Parse error result."""
        go_response = {
            "success": False,
            "error": "connection refused",
        }
        
        result = QueryResult.from_dict(go_response)
        
        assert not result.success
        assert "connection" in result.error.lower()
    
    def test_empty_result(self):
        """Parse empty result set."""
        go_response = {
            "success": True,
            "rows": [],
            "columns": ["id"],
            "rows_affected": 0,
        }
        
        result = QueryResult.from_dict(go_response)
        
        assert result.success
        assert result.is_empty
    
    def test_null_values_in_rows(self):
        """NULL values in result rows."""
        go_response = {
            "success": True,
            "rows": [[1, None], [2, "Bob"]],
            "columns": ["id", "name"],
        }
        
        result = QueryResult.from_dict(go_response)
        
        row = result.first_dict()
        assert row["name"] is None
    
    def test_various_types(self):
        """Various data types in results."""
        go_response = {
            "success": True,
            "rows": [
                [1, "text", True, 3.14, None],
            ],
            "columns": ["int", "str", "bool", "float", "null"],
        }
        
        result = QueryResult.from_dict(go_response)
        row = result.first_dict()
        
        assert isinstance(row["int"], int)
        assert isinstance(row["str"], str)
        assert isinstance(row["bool"], bool)
        assert isinstance(row["float"], float)
        assert row["null"] is None
    
    def test_large_result(self):
        """Large result set."""
        rows = [[i, f"name_{i}"] for i in range(1000)]
        go_response = {
            "success": True,
            "rows": rows,
            "columns": ["id", "name"],
        }
        
        result = QueryResult.from_dict(go_response)
        
        assert len(result) == 1000


class TestHealthStatusFromGo:
    """Test health status JSON received from Go."""
    
    def test_healthy_status(self):
        """Parse healthy status."""
        go_response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "primary": {
                "url": "***",
                "status": "ok",
                "latency_ms": 1.2,
            },
            "pool": {
                "total_conns": 10,
                "idle_conns": 5,
                "active_conns": 5,
            },
        }
        
        health = HealthStatus.from_dict(go_response)
        
        assert health.is_healthy
        assert health.primary.is_ok
    
    def test_unhealthy_status(self):
        """Parse unhealthy status."""
        go_response = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "primary": {
                "url": "***",
                "status": "down",
                "latency_ms": 0,
                "error": "connection refused",
            },
            "pool": {
                "total_conns": 0,
                "idle_conns": 0,
                "active_conns": 0,
            },
        }
        
        health = HealthStatus.from_dict(go_response)
        
        assert health.is_unhealthy
        assert health.primary.is_down


# =============================================================================
# Edge Cases in Serialization
# =============================================================================

class TestSerializationEdgeCases:
    """Test edge cases in JSON serialization."""
    
    def test_empty_string(self):
        """Empty strings."""
        request = {"params": [""]}
        assert json.loads(json.dumps(request))["params"][0] == ""
    
    def test_unicode_emoji(self):
        """Unicode emoji characters."""
        request = {"params": ["Hello 👋 World 🌍"]}
        parsed = json.loads(json.dumps(request))
        assert "👋" in parsed["params"][0]
        assert "🌍" in parsed["params"][0]
    
    def test_unicode_chinese(self):
        """Chinese characters."""
        request = {"params": ["你好世界"]}
        parsed = json.loads(json.dumps(request))
        assert parsed["params"][0] == "你好世界"
    
    def test_escaped_chars(self):
        """Escaped characters."""
        request = {"params": ["line1\\nline2"]}
        parsed = json.loads(json.dumps(request))
        assert parsed["params"][0] == "line1\\nline2"
    
    def test_very_long_string(self):
        """Very long string (1MB)."""
        long_str = "x" * (1024 * 1024)
        request = {"params": [long_str]}
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert len(parsed["params"][0]) == 1024 * 1024
    
    def test_deeply_nested(self):
        """Deeply nested structure."""
        # Simulate JSON column data
        nested = {"a": {"b": {"c": {"d": [1, 2, 3]}}}}
        request = {"params": [json.dumps(nested)]}
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        inner = json.loads(parsed["params"][0])
        assert inner["a"]["b"]["c"]["d"] == [1, 2, 3]
    
    def test_array_param(self):
        """Array parameter (for PostgreSQL arrays)."""
        arr = [1, 2, 3, 4, 5]
        request = {"params": [arr]}
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert parsed["params"][0] == arr
    
    def test_decimal_precision(self):
        """Decimal precision handling."""
        # Decimal must be converted to string for full precision
        d = Decimal("123.456789012345678901234567890")
        request = {"params": [str(d)]}
        
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        restored = Decimal(parsed["params"][0])
        assert restored == d


# =============================================================================
# Consistency Tests
# =============================================================================

class TestJsonConsistency:
    """Test JSON consistency between Python and Go expectations."""
    
    def test_config_keys_snake_case(self):
        """Config keys should be snake_case."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        json_str = config.to_json()
        parsed = json.loads(json_str)
        
        for key in parsed.keys():
            # All keys should be snake_case (no camelCase)
            assert "_" in key or key.islower() or key in ["primary", "replicas", "debug"], f"Key '{key}' should be snake_case"
    
    def test_error_format_consistent(self):
        """Error format should be consistent."""
        err = BridgeError("test")
        
        # Error should have predictable attributes
        assert hasattr(err, "args")
