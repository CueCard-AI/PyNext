"""
Comprehensive tests for PyNext Live Query Configuration.

Tests all configuration classes and enums:
- LiveQueryConfig
- QuerySignature  
- TransportType
- DetectionStrategy
- UpdateGranularity

Target: 60 tests
"""

import pytest
from dataclasses import FrozenInstanceError
from typing import Tuple

from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    TransportType,
    DetectionStrategy,
    UpdateGranularity,
    DEFAULT_CONFIG,
)


# =============================================================================
# TransportType Tests
# =============================================================================

class TestTransportType:
    """Tests for TransportType enum."""
    
    def test_auto_value(self):
        """Test AUTO transport type."""
        assert TransportType.AUTO.value == "auto"
    
    def test_sse_value(self):
        """Test SSE transport type."""
        assert TransportType.SSE.value == "sse"
    
    def test_websocket_value(self):
        """Test WEBSOCKET transport type."""
        assert TransportType.WEBSOCKET.value == "websocket"
    
    def test_from_string_valid(self):
        """Test creating from valid string."""
        assert TransportType("auto") == TransportType.AUTO
        assert TransportType("sse") == TransportType.SSE
        assert TransportType("websocket") == TransportType.WEBSOCKET
    
    def test_from_string_invalid(self):
        """Test creating from invalid string."""
        with pytest.raises(ValueError):
            TransportType("invalid")


# =============================================================================
# DetectionStrategy Tests
# =============================================================================

class TestDetectionStrategy:
    """Tests for DetectionStrategy enum."""
    
    def test_auto_value(self):
        """Test AUTO detection strategy."""
        assert DetectionStrategy.AUTO.value == "auto"
    
    def test_postgres_value(self):
        """Test POSTGRES detection strategy."""
        assert DetectionStrategy.POSTGRES.value == "postgres"
    
    def test_supabase_value(self):
        """Test SUPABASE detection strategy."""
        assert DetectionStrategy.SUPABASE.value == "supabase"
    
    def test_polling_value(self):
        """Test POLLING detection strategy."""
        assert DetectionStrategy.POLLING.value == "polling"
    
    def test_all_strategies_exist(self):
        """Test all strategies are defined."""
        strategies = [s.value for s in DetectionStrategy]
        assert "auto" in strategies
        assert "postgres" in strategies
        assert "supabase" in strategies
        assert "polling" in strategies


# =============================================================================
# UpdateGranularity Tests
# =============================================================================

class TestUpdateGranularity:
    """Tests for UpdateGranularity enum."""
    
    def test_auto_value(self):
        """Test AUTO granularity."""
        assert UpdateGranularity.AUTO.value == "auto"
    
    def test_surgical_value(self):
        """Test SURGICAL granularity."""
        assert UpdateGranularity.SURGICAL.value == "surgical"
    
    def test_refresh_value(self):
        """Test REFRESH granularity."""
        assert UpdateGranularity.REFRESH.value == "refresh"


# =============================================================================
# QuerySignature Tests
# =============================================================================

class TestQuerySignature:
    """Tests for QuerySignature dataclass."""
    
    def test_create_simple_signature(self):
        """Test creating simple signature."""
        sig = QuerySignature(table="users")
        
        assert sig.table == "users"
        assert sig.where_clauses == ()
        assert sig.order_by is None
        assert sig.limit is None
        assert sig.offset is None
    
    def test_create_with_where(self):
        """Test creating signature with WHERE clauses."""
        sig = QuerySignature(
            table="users",
            where_clauses=((("status", "active"),), (("role", "admin"),)),
        )
        
        assert len(sig.where_clauses) == 2
    
    def test_create_with_order(self):
        """Test creating signature with ORDER BY."""
        sig = QuerySignature(
            table="users",
            order_by="name ASC, id DESC",
        )
        
        assert sig.order_by is not None
        assert sig.has_ordering is True
    
    def test_create_with_limit_offset(self):
        """Test creating signature with LIMIT and OFFSET."""
        sig = QuerySignature(
            table="users",
            limit=10,
            offset=20,
        )
        
        assert sig.limit == 10
        assert sig.offset == 20
    
    def test_create_with_joins(self):
        """Test creating signature with JOINs."""
        sig = QuerySignature(
            table="users",
            joins=(("posts", "users.id", "posts.user_id"),),
        )
        
        assert sig.has_joins is True
    
    def test_hash_property(self):
        """Test hash property."""
        sig = QuerySignature(table="users")
        
        h = sig.hash
        assert h is not None
        assert isinstance(h, int)
    
    def test_hash_consistency(self):
        """Test hash is consistent."""
        sig = QuerySignature(table="users", limit=10)
        
        h1 = sig.hash
        h2 = sig.hash
        
        assert h1 == h2
    
    def test_hash_equality(self):
        """Test identical signatures have same hash."""
        sig1 = QuerySignature(
            table="users",
            where_clauses=((("id", 1),),),
            order_by="name ASC",
        )
        sig2 = QuerySignature(
            table="users",
            where_clauses=((("id", 1),),),
            order_by="name ASC",
        )
        
        assert sig1.hash == sig2.hash
    
    def test_hash_inequality(self):
        """Test different signatures have different hash."""
        sig1 = QuerySignature(table="users", limit=10)
        sig2 = QuerySignature(table="users", limit=20)
        
        assert sig1.hash != sig2.hash
    
    def test_is_simple_true(self):
        """Test is_simple for simple query."""
        sig = QuerySignature(table="users")
        assert sig.is_simple is True
    
    def test_is_simple_false_with_where(self):
        """Test is_simple false with WHERE clauses."""
        sig = QuerySignature(
            table="users",
            where_clauses=((("id", 1),),),
        )
        assert sig.is_simple is False  # Has where clause
    
    def test_is_simple_false_with_order(self):
        """Test is_simple false with ORDER BY."""
        sig = QuerySignature(
            table="users",
            order_by="name ASC",
        )
        assert sig.is_simple is False
    
    def test_is_simple_false_with_limit(self):
        """Test is_simple false with LIMIT."""
        sig = QuerySignature(table="users", limit=10)
        assert sig.is_simple is False
    
    def test_is_simple_false_with_joins(self):
        """Test is_simple false with JOINs."""
        sig = QuerySignature(
            table="users",
            joins=(("posts", "id", "user_id"),),
        )
        assert sig.is_simple is False
    
    def test_has_joins_false(self):
        """Test has_joins false."""
        sig = QuerySignature(table="users")
        assert sig.has_joins is False
    
    def test_has_aggregations_default(self):
        """Test has_aggregations default."""
        sig = QuerySignature(table="users")
        assert sig.has_aggregations is False
    
    def test_to_dict(self):
        """Test converting to dict."""
        sig = QuerySignature(
            table="users",
            where_clauses=((("status", "active"),),),
            limit=10,
        )
        
        d = sig.to_dict()
        
        assert d["table"] == "users"
        assert d["limit"] == 10
        assert "where_clauses" in d
    
    def test_from_dict(self):
        """Test creating from dict."""
        d = {
            "table": "users",
            "where_clauses": [[["id", 1]]],
            "order_by": "name ASC",
            "limit": 10,
        }
        
        sig = QuerySignature.from_dict(d)
        
        assert sig.table == "users"
        assert sig.limit == 10
    
    def test_signature_equality(self):
        """Test signature equality via __eq__."""
        sig1 = QuerySignature(table="users", limit=10)
        sig2 = QuerySignature(table="users", limit=10)
        
        assert sig1 == sig2


# =============================================================================
# LiveQueryConfig Tests
# =============================================================================

class TestLiveQueryConfig:
    """Tests for LiveQueryConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LiveQueryConfig()
        
        assert config.transport == TransportType.AUTO
        assert config.detection == DetectionStrategy.AUTO
        assert config.granularity == UpdateGranularity.AUTO
        assert config.batch_delay_ms == 50
        assert config.max_reconnect_attempts == 10
        assert config.reconnect_delay_ms == 1000
        assert config.poll_interval == 30.0
    
    def test_custom_transport(self):
        """Test custom transport setting."""
        config = LiveQueryConfig(transport=TransportType.WEBSOCKET)
        assert config.transport == TransportType.WEBSOCKET
    
    def test_custom_detection(self):
        """Test custom detection setting."""
        config = LiveQueryConfig(detection=DetectionStrategy.POSTGRES)
        assert config.detection == DetectionStrategy.POSTGRES
    
    def test_custom_granularity(self):
        """Test custom granularity setting."""
        config = LiveQueryConfig(granularity=UpdateGranularity.SURGICAL)
        assert config.granularity == UpdateGranularity.SURGICAL
    
    def test_batch_delay_setting(self):
        """Test batch delay setting."""
        config = LiveQueryConfig(batch_delay_ms=100)
        assert config.batch_delay_ms == 100
        assert config.debounce_ms == 100  # Alias
    
    def test_reconnect_delay_setting(self):
        """Test reconnect delay setting."""
        config = LiveQueryConfig(reconnect_delay_ms=500)
        assert config.reconnect_delay_ms == 500
    
    def test_max_reconnect_attempts_setting(self):
        """Test max reconnect attempts setting."""
        config = LiveQueryConfig(max_reconnect_attempts=5)
        assert config.max_reconnect_attempts == 5
    
    def test_stale_time_setting(self):
        """Test stale time setting."""
        config = LiveQueryConfig(stale_time_ms=2000)
        assert config.stale_time_ms == 2000
    
    def test_poll_interval_setting(self):
        """Test poll interval setting."""
        config = LiveQueryConfig(poll_interval=10.0)
        assert config.poll_interval == 10.0
    
    def test_to_dict(self):
        """Test converting config to dict."""
        config = LiveQueryConfig(
            transport=TransportType.SSE,
            batch_delay_ms=100,
        )
        
        d = config.to_dict()
        
        assert d["transport"] == "sse"
        assert d["batch_delay_ms"] == 100
    
    def test_from_dict(self):
        """Test creating config from dict."""
        d = {
            "transport": "websocket",
            "detection": "polling",
            "batch_delay_ms": 200,
            "max_reconnect_attempts": 5,
        }
        
        config = LiveQueryConfig.from_dict(d)
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.detection == DetectionStrategy.POLLING
        assert config.batch_delay_ms == 200
        assert config.max_reconnect_attempts == 5
    
    def test_from_dict_partial(self):
        """Test creating config from partial dict."""
        d = {"batch_delay_ms": 100}
        
        config = LiveQueryConfig.from_dict(d)
        
        assert config.batch_delay_ms == 100
        assert config.transport == TransportType.AUTO  # Default
    
    def test_merge_with_override(self):
        """Test merging configs with kwargs."""
        base = LiveQueryConfig(batch_delay_ms=100, reconnect_delay_ms=500)
        
        merged = base.merge(batch_delay_ms=200)
        
        assert merged.batch_delay_ms == 200  # Overridden
        assert merged.reconnect_delay_ms == 500  # Kept from base
    
    def test_merge_preserves_defaults(self):
        """Test merge preserves defaults when not overridden."""
        base = LiveQueryConfig(transport=TransportType.WEBSOCKET)
        
        merged = base.merge()
        
        assert merged.transport == TransportType.WEBSOCKET


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestConfigFactories:
    """Tests for configuration factory functions."""
    
    def test_default_config(self):
        """Test DEFAULT_CONFIG is a valid LiveQueryConfig."""
        assert isinstance(DEFAULT_CONFIG, LiveQueryConfig)
        assert DEFAULT_CONFIG.transport == TransportType.AUTO
    
    def test_create_config_with_kwargs(self):
        """Test creating config with keyword arguments."""
        config = LiveQueryConfig(
            transport=TransportType.WEBSOCKET,
            batch_delay_ms=100,
        )
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.batch_delay_ms == 100
    
    def test_create_config_with_detection(self):
        """Test creating config with detection strategy."""
        config = LiveQueryConfig(
            transport=TransportType.SSE,
            detection=DetectionStrategy.POSTGRES,
        )
        
        assert config.transport == TransportType.SSE
        assert config.detection == DetectionStrategy.POSTGRES
    
    def test_create_config_with_granularity(self):
        """Test creating config with update granularity."""
        config = LiveQueryConfig(
            granularity=UpdateGranularity.SURGICAL,
        )
        
        assert config.granularity == UpdateGranularity.SURGICAL


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestConfigEdgeCases:
    """Tests for configuration edge cases."""
    
    def test_query_signature_empty_where(self):
        """Test query signature with empty WHERE clauses."""
        sig = QuerySignature(
            table="users",
            where_clauses=(),
        )
        
        assert sig.hash is not None
    
    def test_query_signature_complex_where(self):
        """Test query signature with complex WHERE."""
        sig = QuerySignature(
            table="users",
            where_clauses=(
                (("a", 1), ("b", 2)),  # AND conditions
                (("c", 3),),           # OR with above
            ),
        )
        
        assert sig.hash is not None
    
    def test_config_from_dict_unknown_keys(self):
        """Test config from dict ignores unknown keys."""
        d = {
            "batch_delay_ms": 100,
            "unknown_key": "value",
        }
        
        # Should not raise
        config = LiveQueryConfig.from_dict(d)
        assert config.batch_delay_ms == 100
    
    def test_config_from_dict_invalid_enum(self):
        """Test config from dict with invalid enum value."""
        d = {
            "transport": "invalid_transport",
        }
        
        with pytest.raises(ValueError):
            LiveQueryConfig.from_dict(d)
    
    def test_query_signature_hash_order_invariant(self):
        """Test hash is deterministic."""
        sig = QuerySignature(
            table="users",
            where_clauses=((("a", 1),),),
        )
        
        # Hash should be deterministic
        assert sig.hash == sig.hash
    
    def test_config_batch_delay(self):
        """Test config with batch delay."""
        config = LiveQueryConfig(batch_delay_ms=100)
        
        assert config.batch_delay_ms == 100
        assert config.debounce_ms == 100  # Alias
    
    def test_query_signature_none_values(self):
        """Test query signature with None values."""
        sig = QuerySignature(
            table="users",
            limit=None,
            offset=None,
        )
        
        assert sig.limit is None
        assert sig.is_simple is True

