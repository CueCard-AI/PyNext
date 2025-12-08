"""
Unit tests for Go Bridge configuration.

Tests BridgeConfig validation, serialization, and presets.
"""

import pytest
import json

from pynext_go.config import (
    BridgeConfig,
    DEFAULT_POOL_MIN,
    DEFAULT_POOL_MAX,
    DEFAULT_QUERY_TIMEOUT,
    DEFAULT_POOL_IDLE_TIME,
    DEFAULT_POOL_LIFETIME,
    DEFAULT_HEALTH_INTERVAL,
    DEFAULT_STATEMENT_CACHE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF,
    development_config,
    production_config,
    high_throughput_config,
)


class TestBridgeConfigBasic:
    """Basic configuration tests."""
    
    def test_minimal_config(self):
        """Config with only required primary DSN."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        assert config.primary == "postgresql://localhost/test"
        assert config.replicas == []
        assert config.pool_min_size == DEFAULT_POOL_MIN
        assert config.pool_max_size == DEFAULT_POOL_MAX
    
    def test_full_config(self):
        """Config with all options specified."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            replicas=["postgresql://replica1/test", "postgresql://replica2/test"],
            pool_min_size=5,
            pool_max_size=20,
            pool_max_idle_time=600,
            pool_max_lifetime=7200,
            pool_health_interval=60,
            query_timeout=10000,
            statement_cache=512,
            max_retries=5,
            retry_backoff_ms=200,
            enable_arrow=False,
            enable_prepared=False,
            enable_batch=False,
            debug=True,
        )
        assert config.pool_min_size == 5
        assert config.pool_max_size == 20
        assert config.query_timeout == 10000
        assert config.debug is True
        assert len(config.replicas) == 2
    
    def test_default_values(self):
        """Verify all default values match constants."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        assert config.pool_min_size == DEFAULT_POOL_MIN
        assert config.pool_max_size == DEFAULT_POOL_MAX
        assert config.pool_max_idle_time == DEFAULT_POOL_IDLE_TIME
        assert config.pool_max_lifetime == DEFAULT_POOL_LIFETIME
        assert config.pool_health_interval == DEFAULT_HEALTH_INTERVAL
        assert config.query_timeout == DEFAULT_QUERY_TIMEOUT
        assert config.statement_cache == DEFAULT_STATEMENT_CACHE
        assert config.max_retries == DEFAULT_MAX_RETRIES
        assert config.retry_backoff_ms == DEFAULT_RETRY_BACKOFF
        assert config.enable_arrow is True
        assert config.enable_prepared is True
        assert config.enable_batch is True
        assert config.debug is False


class TestBridgeConfigValidation:
    """Configuration validation tests."""
    
    def test_empty_primary_raises(self):
        """Empty primary DSN should raise."""
        with pytest.raises(ValueError, match="primary connection string is required"):
            BridgeConfig(primary="")
    
    def test_none_primary_raises(self):
        """None primary should fail type check or validation."""
        with pytest.raises((ValueError, TypeError)):
            BridgeConfig(primary=None)  # type: ignore
    
    def test_invalid_primary_format(self):
        """Non-PostgreSQL DSN should raise."""
        with pytest.raises(ValueError, match="must be a PostgreSQL connection string"):
            BridgeConfig(primary="mysql://localhost/test")
    
    def test_postgres_prefix_accepted(self):
        """Both postgresql:// and postgres:// should be accepted."""
        config1 = BridgeConfig(primary="postgresql://localhost/test")
        config2 = BridgeConfig(primary="postgres://localhost/test")
        assert config1.primary.startswith("postgresql://")
        assert config2.primary.startswith("postgres://")
    
    def test_negative_pool_min_raises(self):
        """Negative pool_min_size should raise."""
        with pytest.raises(ValueError, match="pool_min_size must be >= 0"):
            BridgeConfig(primary="postgresql://localhost/test", pool_min_size=-1)
    
    def test_zero_pool_min_allowed(self):
        """pool_min_size=0 is valid (lazy pool)."""
        config = BridgeConfig(primary="postgresql://localhost/test", pool_min_size=0)
        assert config.pool_min_size == 0
    
    def test_zero_pool_max_raises(self):
        """pool_max_size=0 should raise (need at least 1)."""
        with pytest.raises(ValueError, match="pool_max_size must be >= 1"):
            BridgeConfig(primary="postgresql://localhost/test", pool_max_size=0)
    
    def test_pool_min_greater_than_max_raises(self):
        """pool_min_size > pool_max_size should raise."""
        with pytest.raises(ValueError, match="pool_min_size .* cannot exceed"):
            BridgeConfig(
                primary="postgresql://localhost/test",
                pool_min_size=10,
                pool_max_size=5,
            )
    
    def test_pool_min_equal_max_allowed(self):
        """pool_min_size == pool_max_size is valid (fixed size pool)."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=5,
            pool_max_size=5,
        )
        assert config.pool_min_size == config.pool_max_size
    
    def test_negative_timeout_raises(self):
        """Negative timeout should raise."""
        with pytest.raises(ValueError, match="query_timeout must be >= 0"):
            BridgeConfig(primary="postgresql://localhost/test", query_timeout=-1)
    
    def test_zero_timeout_allowed(self):
        """query_timeout=0 means no timeout (infinite wait)."""
        config = BridgeConfig(primary="postgresql://localhost/test", query_timeout=0)
        assert config.query_timeout == 0
    
    def test_negative_statement_cache_raises(self):
        """Negative statement cache should raise."""
        with pytest.raises(ValueError, match="statement_cache must be >= 0"):
            BridgeConfig(primary="postgresql://localhost/test", statement_cache=-1)
    
    def test_negative_max_retries_raises(self):
        """Negative max_retries should raise."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            BridgeConfig(primary="postgresql://localhost/test", max_retries=-1)
    
    def test_invalid_replica_format(self):
        """Invalid replica DSN format should raise."""
        with pytest.raises(ValueError, match="replica\\[0\\] must be a PostgreSQL"):
            BridgeConfig(
                primary="postgresql://localhost/test",
                replicas=["mysql://replica/test"],
            )


class TestBridgeConfigSerialization:
    """Configuration serialization tests."""
    
    def test_to_dict(self):
        """to_dict should produce valid dict with all fields."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        d = config.to_dict()
        
        assert isinstance(d, dict)
        assert d["primary"] == "postgresql://localhost/test"
        assert d["pool_min_size"] == DEFAULT_POOL_MIN
        assert d["pool_max_size"] == DEFAULT_POOL_MAX
        assert d["enable_arrow"] is True
    
    def test_to_json(self):
        """to_json should produce valid JSON."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        j = config.to_json()
        
        assert isinstance(j, str)
        data = json.loads(j)
        assert data["primary"] == "postgresql://localhost/test"
    
    def test_from_dict(self):
        """from_dict should create valid config."""
        d = {
            "primary": "postgresql://localhost/test",
            "pool_max_size": 20,
        }
        config = BridgeConfig.from_dict(d)
        
        assert config.primary == "postgresql://localhost/test"
        assert config.pool_max_size == 20
        assert config.pool_min_size == DEFAULT_POOL_MIN  # Default
    
    def test_from_json(self):
        """from_json should create valid config."""
        j = '{"primary": "postgresql://localhost/test", "debug": true}'
        config = BridgeConfig.from_json(j)
        
        assert config.primary == "postgresql://localhost/test"
        assert config.debug is True
    
    def test_roundtrip(self):
        """Config should survive JSON roundtrip."""
        original = BridgeConfig(
            primary="postgresql://localhost/test",
            replicas=["postgresql://replica/test"],
            pool_max_size=30,
            query_timeout=5000,
            debug=True,
        )
        
        j = original.to_json()
        restored = BridgeConfig.from_json(j)
        
        assert restored.primary == original.primary
        assert restored.replicas == original.replicas
        assert restored.pool_max_size == original.pool_max_size
        assert restored.query_timeout == original.query_timeout
        assert restored.debug == original.debug
    
    def test_json_field_names_snake_case(self):
        """JSON should use snake_case for Go compatibility."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        d = config.to_dict()
        
        # Check snake_case field names
        assert "pool_min_size" in d
        assert "pool_max_size" in d
        assert "query_timeout" in d
        assert "enable_arrow" in d
        assert "poolMinSize" not in d  # Not camelCase


class TestBridgeConfigModifiers:
    """Configuration modifier method tests."""
    
    def test_with_pool(self):
        """with_pool should create new config with modified pool settings."""
        original = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=2,
            pool_max_size=10,
        )
        
        modified = original.with_pool(min_size=5, max_size=25)
        
        # Original unchanged
        assert original.pool_min_size == 2
        assert original.pool_max_size == 10
        
        # Modified has new values
        assert modified.pool_min_size == 5
        assert modified.pool_max_size == 25
        
        # Other values preserved
        assert modified.primary == original.primary
    
    def test_with_pool_partial(self):
        """with_pool with partial args should preserve other values."""
        original = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_min_size=2,
            pool_max_size=10,
            pool_max_idle_time=300,
        )
        
        modified = original.with_pool(max_size=20)
        
        assert modified.pool_min_size == 2  # Preserved
        assert modified.pool_max_size == 20  # Changed
        assert modified.pool_max_idle_time == 300  # Preserved
    
    def test_with_timeout(self):
        """with_timeout should create new config with modified timeout."""
        original = BridgeConfig(
            primary="postgresql://localhost/test",
            query_timeout=30000,
        )
        
        modified = original.with_timeout(5000)
        
        # Original unchanged
        assert original.query_timeout == 30000
        
        # Modified has new value
        assert modified.query_timeout == 5000
        
        # Other values preserved
        assert modified.primary == original.primary
        assert modified.pool_max_size == original.pool_max_size


class TestBridgeConfigPresets:
    """Preset configuration tests."""
    
    def test_development_config(self):
        """Development config should have small pool and debug enabled."""
        config = development_config("postgresql://localhost/dev")
        
        assert config.primary == "postgresql://localhost/dev"
        assert config.pool_min_size == 1
        assert config.pool_max_size == 5
        assert config.query_timeout == 5000
        assert config.debug is True
    
    def test_production_config(self):
        """Production config should have larger pool and debug disabled."""
        config = production_config("postgresql://localhost/prod")
        
        assert config.primary == "postgresql://localhost/prod"
        assert config.pool_min_size == 5
        assert config.pool_max_size == 20
        assert config.query_timeout == 30000
        assert config.debug is False
    
    def test_production_config_with_replicas(self):
        """Production config should support replicas."""
        config = production_config(
            "postgresql://localhost/prod",
            replicas=["postgresql://replica1/prod", "postgresql://replica2/prod"],
        )
        
        assert len(config.replicas) == 2
    
    def test_high_throughput_config(self):
        """High throughput config should have large pool and caching."""
        config = high_throughput_config("postgresql://localhost/prod")
        
        assert config.pool_min_size == 10
        assert config.pool_max_size == 50
        assert config.statement_cache == 1024
        assert config.enable_batch is True


class TestBridgeConfigEdgeCases:
    """Edge case tests."""
    
    def test_unicode_in_dsn(self):
        """DSN with unicode characters should work."""
        config = BridgeConfig(primary="postgresql://user:pässwörd@localhost/test")
        assert "pässwörd" in config.primary
    
    def test_special_chars_in_password(self):
        """DSN with special characters in password should work."""
        config = BridgeConfig(primary="postgresql://user:p%40ss%3Dword@localhost/test")
        assert config.primary == "postgresql://user:p%40ss%3Dword@localhost/test"
    
    def test_empty_replicas_list(self):
        """Empty replicas list should be valid."""
        config = BridgeConfig(primary="postgresql://localhost/test", replicas=[])
        assert config.replicas == []
    
    def test_large_pool_values(self):
        """Very large pool values should be accepted."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            pool_max_size=1000,
            statement_cache=10000,
        )
        assert config.pool_max_size == 1000
        assert config.statement_cache == 10000
    
    def test_very_long_timeout(self):
        """Very long timeout (1 hour) should be accepted."""
        config = BridgeConfig(
            primary="postgresql://localhost/test",
            query_timeout=3600000,  # 1 hour in ms
        )
        assert config.query_timeout == 3600000


class TestBridgeConfigConstants:
    """Constant value tests."""
    
    def test_default_pool_min(self):
        """DEFAULT_POOL_MIN should be reasonable."""
        assert DEFAULT_POOL_MIN >= 0
        assert DEFAULT_POOL_MIN <= 10
    
    def test_default_pool_max(self):
        """DEFAULT_POOL_MAX should be reasonable."""
        assert DEFAULT_POOL_MAX >= DEFAULT_POOL_MIN
        assert DEFAULT_POOL_MAX <= 100
    
    def test_default_timeout(self):
        """DEFAULT_QUERY_TIMEOUT should be reasonable (10s - 60s)."""
        assert DEFAULT_QUERY_TIMEOUT >= 10000  # At least 10s
        assert DEFAULT_QUERY_TIMEOUT <= 60000  # At most 60s
    
    def test_defaults_consistent(self):
        """Default constants should match config defaults."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        assert config.pool_min_size == DEFAULT_POOL_MIN
        assert config.pool_max_size == DEFAULT_POOL_MAX
        assert config.query_timeout == DEFAULT_QUERY_TIMEOUT

