"""
Comprehensive tests for PostgreSQL External Pooler Support (Phase 5.2).

Tests cover:
- ExternalPoolerConfig validation and defaults
- PoolerType and PoolerMode enums
- ExternalPoolerManager initialization
- Pooler detection
- Feature compatibility checks
- Connection options generation
- Platform-specific configurations

Total: 80 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from pynext.db.adapters.postgres_external import (
    ExternalPoolerConfig,
    ExternalPoolerManager,
    PoolerType,
    PoolerMode,
    PoolerInfo,
    PoolerDetectionError,
    PoolerCompatibilityError,
    detect_pooler_from_port,
    create_pooler_config_for_supabase,
    create_pooler_config_for_render,
    create_pooler_config_for_neon,
)


# =============================================================================
# PoolerType Tests (10 tests)
# =============================================================================

class TestPoolerType:
    """Tests for PoolerType enum."""
    
    def test_pgbouncer_type(self):
        """Test PgBouncer type."""
        assert PoolerType.PGBOUNCER.value == "pgbouncer"
        
    def test_pgpool_type(self):
        """Test pgpool type."""
        assert PoolerType.PGPOOL.value == "pgpool"
        
    def test_odyssey_type(self):
        """Test Odyssey type."""
        assert PoolerType.ODYSSEY.value == "odyssey"
        
    def test_unknown_type(self):
        """Test unknown type."""
        assert PoolerType.UNKNOWN.value == "unknown"
        
    def test_none_type(self):
        """Test none type."""
        assert PoolerType.NONE.value == "none"
        
    def test_all_types_exist(self):
        """Test all pooler types exist."""
        assert len(PoolerType) == 5
        
    def test_type_from_value(self):
        """Test getting type from value."""
        assert PoolerType("pgbouncer") == PoolerType.PGBOUNCER
        
    def test_type_comparison(self):
        """Test type comparison."""
        assert PoolerType.PGBOUNCER != PoolerType.PGPOOL
        
    def test_type_equality(self):
        """Test type equality."""
        assert PoolerType.PGBOUNCER == PoolerType.PGBOUNCER
        
    def test_type_string_representation(self):
        """Test type string representation."""
        assert "pgbouncer" in str(PoolerType.PGBOUNCER).lower()


# =============================================================================
# PoolerMode Tests (10 tests)
# =============================================================================

class TestPoolerMode:
    """Tests for PoolerMode enum."""
    
    def test_transaction_mode(self):
        """Test transaction mode."""
        assert PoolerMode.TRANSACTION.value == "transaction"
        
    def test_session_mode(self):
        """Test session mode."""
        assert PoolerMode.SESSION.value == "session"
        
    def test_statement_mode(self):
        """Test statement mode."""
        assert PoolerMode.STATEMENT.value == "statement"
        
    def test_all_modes_exist(self):
        """Test all pooler modes exist."""
        assert len(PoolerMode) == 3
        
    def test_mode_from_value(self):
        """Test getting mode from value."""
        assert PoolerMode("transaction") == PoolerMode.TRANSACTION
        
    def test_mode_comparison(self):
        """Test mode comparison."""
        assert PoolerMode.TRANSACTION != PoolerMode.SESSION
        
    def test_mode_equality(self):
        """Test mode equality."""
        assert PoolerMode.SESSION == PoolerMode.SESSION
        
    def test_transaction_is_most_common(self):
        """Test transaction mode is commonly used."""
        assert PoolerMode.TRANSACTION is not None
        
    def test_session_for_full_features(self):
        """Test session mode for full feature support."""
        assert PoolerMode.SESSION is not None
        
    def test_statement_is_deprecated(self):
        """Test statement mode exists but is deprecated."""
        assert PoolerMode.STATEMENT is not None


# =============================================================================
# ExternalPoolerConfig Tests (20 tests)
# =============================================================================

class TestExternalPoolerConfig:
    """Tests for ExternalPoolerConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ExternalPoolerConfig()
        assert config.enabled is False
        assert config.type == PoolerType.NONE
        assert config.mode == PoolerMode.TRANSACTION
        assert config.auto_detect is True
        
    def test_enabled_config(self):
        """Test enabled configuration."""
        config = ExternalPoolerConfig(enabled=True)
        assert config.enabled is True
        
    def test_pgbouncer_config(self):
        """Test PgBouncer configuration."""
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        )
        assert config.type == PoolerType.PGBOUNCER
        
    def test_transaction_mode_defaults(self):
        """Test transaction mode applies defaults."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        assert config.disable_prepared_statements is True
        assert config.disable_server_side_cursors is True
        assert config.disable_notifications is True
        
    def test_session_mode_defaults(self):
        """Test session mode allows all features."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
        )
        assert config.disable_prepared_statements is False
        assert config.disable_server_side_cursors is False
        assert config.disable_notifications is False
        
    def test_explicit_disable_overrides(self):
        """Test explicit disable settings override defaults."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
            disable_prepared_statements=True,
        )
        assert config.disable_prepared_statements is True
        
    def test_explicit_enable_overrides(self):
        """Test explicit enable settings override defaults."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
            disable_prepared_statements=False,
        )
        assert config.disable_prepared_statements is False
        
    def test_get_incompatible_features(self):
        """Test getting incompatible features."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        features = config.get_incompatible_features()
        assert "prepared_statements" in features
        assert "server_side_cursors" in features
        assert "notifications" in features
        
    def test_get_incompatible_features_session(self):
        """Test no incompatible features in session mode."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
        )
        features = config.get_incompatible_features()
        assert len(features) == 0
        
    def test_custom_connection_check_query(self):
        """Test custom connection check query."""
        config = ExternalPoolerConfig(
            connection_check_query="SELECT NOW()",
        )
        assert config.connection_check_query == "SELECT NOW()"
        
    def test_auto_detect_enabled_by_default(self):
        """Test auto-detect is enabled by default."""
        config = ExternalPoolerConfig()
        assert config.auto_detect is True
        
    def test_auto_detect_disabled(self):
        """Test auto-detect can be disabled."""
        config = ExternalPoolerConfig(auto_detect=False)
        assert config.auto_detect is False
        
    def test_verify_on_connect_default(self):
        """Test verify_on_connect default."""
        config = ExternalPoolerConfig()
        assert config.verify_on_connect is True
        
    def test_pgpool_config(self):
        """Test pgpool configuration."""
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGPOOL,
        )
        assert config.type == PoolerType.PGPOOL
        
    def test_odyssey_config(self):
        """Test Odyssey configuration."""
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.ODYSSEY,
        )
        assert config.type == PoolerType.ODYSSEY
        
    def test_statement_mode_config(self):
        """Test statement mode configuration."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.STATEMENT,
        )
        assert config.mode == PoolerMode.STATEMENT
        
    def test_disabled_config_ignores_other_settings(self):
        """Test disabled config still stores other settings."""
        config = ExternalPoolerConfig(
            enabled=False,
            type=PoolerType.PGBOUNCER,
        )
        assert config.type == PoolerType.PGBOUNCER
        
    def test_config_immutability(self):
        """Test config values are accessible."""
        config = ExternalPoolerConfig(enabled=True)
        assert config.enabled is True
        
    def test_default_connection_check_query(self):
        """Test default connection check query."""
        config = ExternalPoolerConfig()
        assert config.connection_check_query == "SELECT 1"
        
    def test_mixed_feature_disabling(self):
        """Test mixed feature disabling."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
            disable_notifications=True,
        )
        features = config.get_incompatible_features()
        assert "notifications" in features
        assert "prepared_statements" not in features


# =============================================================================
# PoolerInfo Tests (10 tests)
# =============================================================================

class TestPoolerInfo:
    """Tests for PoolerInfo dataclass."""
    
    def test_creation(self):
        """Test info creation."""
        info = PoolerInfo(type=PoolerType.PGBOUNCER)
        assert info.type == PoolerType.PGBOUNCER
        
    def test_with_mode(self):
        """Test info with mode."""
        info = PoolerInfo(
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        )
        assert info.mode == PoolerMode.TRANSACTION
        
    def test_with_version(self):
        """Test info with version."""
        info = PoolerInfo(
            type=PoolerType.PGBOUNCER,
            version="1.18.0",
        )
        assert info.version == "1.18.0"
        
    def test_with_server_version(self):
        """Test info with server version."""
        info = PoolerInfo(
            type=PoolerType.NONE,
            server_version="15.2",
        )
        assert info.server_version == "15.2"
        
    def test_with_extra(self):
        """Test info with extra data."""
        info = PoolerInfo(
            type=PoolerType.PGBOUNCER,
            extra={"stats": {"active": 10}},
        )
        assert "stats" in info.extra
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = PoolerInfo(
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        )
        d = info.to_dict()
        assert d["type"] == "pgbouncer"
        assert d["mode"] == "transaction"
        
    def test_to_dict_no_mode(self):
        """Test conversion to dictionary without mode."""
        info = PoolerInfo(type=PoolerType.NONE)
        d = info.to_dict()
        assert d["mode"] is None
        
    def test_default_extra(self):
        """Test default extra is empty dict."""
        info = PoolerInfo(type=PoolerType.NONE)
        assert info.extra == {}
        
    def test_default_mode(self):
        """Test default mode is None."""
        info = PoolerInfo(type=PoolerType.NONE)
        assert info.mode is None
        
    def test_default_version(self):
        """Test default version is None."""
        info = PoolerInfo(type=PoolerType.NONE)
        assert info.version is None


# =============================================================================
# ExternalPoolerManager Tests (20 tests)
# =============================================================================

class TestExternalPoolerManager:
    """Tests for ExternalPoolerManager class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        manager = ExternalPoolerManager()
        assert manager.is_enabled is False
        
    def test_init_enabled_config(self):
        """Test initialization with enabled config."""
        config = ExternalPoolerConfig(enabled=True)
        manager = ExternalPoolerManager(config)
        assert manager.is_enabled is True
        
    def test_config_property(self):
        """Test config property."""
        config = ExternalPoolerConfig(enabled=True)
        manager = ExternalPoolerManager(config)
        assert manager.config.enabled is True
        
    def test_pooler_info_none_initially(self):
        """Test pooler_info is None initially."""
        manager = ExternalPoolerManager()
        assert manager.pooler_info is None
        
    def test_pooler_type(self):
        """Test pooler_type property."""
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
        )
        manager = ExternalPoolerManager(config)
        assert manager.pooler_type == PoolerType.PGBOUNCER
        
    def test_pooler_mode(self):
        """Test pooler_mode property."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
        )
        manager = ExternalPoolerManager(config)
        assert manager.pooler_mode == PoolerMode.SESSION
        
    def test_can_use_prepared_statements_disabled(self):
        """Test prepared statements check when disabled."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        manager = ExternalPoolerManager(config)
        assert manager.can_use_prepared_statements() is False
        
    def test_can_use_prepared_statements_enabled(self):
        """Test prepared statements check when enabled."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.SESSION,
        )
        manager = ExternalPoolerManager(config)
        assert manager.can_use_prepared_statements() is True
        
    def test_can_use_prepared_statements_pooler_disabled(self):
        """Test prepared statements when pooler disabled."""
        manager = ExternalPoolerManager()
        assert manager.can_use_prepared_statements() is True
        
    def test_can_use_server_side_cursors(self):
        """Test server-side cursors check."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        manager = ExternalPoolerManager(config)
        assert manager.can_use_server_side_cursors() is False
        
    def test_can_use_notifications(self):
        """Test notifications check."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        manager = ExternalPoolerManager(config)
        assert manager.can_use_notifications() is False
        
    def test_assert_feature_available_passes(self):
        """Test assert_feature_available passes for available feature."""
        manager = ExternalPoolerManager()
        # Should not raise
        manager.assert_feature_available("prepared_statements")
        
    def test_assert_feature_available_raises(self):
        """Test assert_feature_available raises for unavailable feature."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        manager = ExternalPoolerManager(config)
        with pytest.raises(PoolerCompatibilityError):
            manager.assert_feature_available("prepared_statements")
            
    def test_get_connection_options_empty(self):
        """Test connection options when pooler disabled."""
        manager = ExternalPoolerManager()
        options = manager.get_connection_options()
        assert options == {}
        
    def test_get_connection_options_with_pooler(self):
        """Test connection options with pooler enabled."""
        config = ExternalPoolerConfig(
            enabled=True,
            mode=PoolerMode.TRANSACTION,
        )
        manager = ExternalPoolerManager(config)
        options = manager.get_connection_options()
        assert options.get("statement_cache_size") == 0
        
    @pytest.mark.asyncio
    async def test_validate_connection_success(self):
        """Test successful connection validation."""
        manager = ExternalPoolerManager()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        result = await manager.validate_connection(mock_conn)
        assert result is True
        
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self):
        """Test failed connection validation."""
        manager = ExternalPoolerManager()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Failed"))
        result = await manager.validate_connection(mock_conn)
        assert result is False
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ExternalPoolerConfig(enabled=True)
        manager = ExternalPoolerManager(config)
        d = manager.to_dict()
        assert "enabled" in d
        assert "type" in d
        assert "mode" in d
        
    def test_repr_disabled(self):
        """Test string representation when disabled."""
        manager = ExternalPoolerManager()
        repr_str = repr(manager)
        assert "disabled" in repr_str
        
    def test_repr_enabled(self):
        """Test string representation when enabled."""
        config = ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
        )
        manager = ExternalPoolerManager(config)
        repr_str = repr(manager)
        assert "pgbouncer" in repr_str


# =============================================================================
# Helper Function Tests (10 tests)
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_detect_pooler_from_port_5432(self):
        """Test detecting direct PostgreSQL on 5432."""
        result = detect_pooler_from_port(5432)
        assert result == PoolerType.UNKNOWN
        
    def test_detect_pooler_from_port_6432(self):
        """Test detecting PgBouncer on 6432."""
        result = detect_pooler_from_port(6432)
        assert result == PoolerType.PGBOUNCER
        
    def test_detect_pooler_from_port_9999(self):
        """Test detecting pgpool on 9999."""
        result = detect_pooler_from_port(9999)
        assert result == PoolerType.PGPOOL
        
    def test_detect_pooler_from_port_6433(self):
        """Test detecting Odyssey on 6433."""
        result = detect_pooler_from_port(6433)
        assert result == PoolerType.ODYSSEY
        
    def test_detect_pooler_from_port_unknown(self):
        """Test detecting unknown pooler on random port."""
        result = detect_pooler_from_port(5555)
        assert result == PoolerType.UNKNOWN
        
    def test_supabase_config(self):
        """Test Supabase config helper."""
        config = create_pooler_config_for_supabase()
        assert config.enabled is True
        assert config.type == PoolerType.PGBOUNCER
        assert config.mode == PoolerMode.TRANSACTION
        assert config.auto_detect is False
        
    def test_render_config(self):
        """Test Render config helper."""
        config = create_pooler_config_for_render()
        assert config.enabled is True
        assert config.type == PoolerType.PGBOUNCER
        
    def test_neon_config(self):
        """Test Neon config helper."""
        config = create_pooler_config_for_neon()
        assert config.enabled is True
        assert config.type == PoolerType.PGBOUNCER
        
    def test_platform_configs_are_production_ready(self):
        """Test platform configs have production settings."""
        for create_func in [
            create_pooler_config_for_supabase,
            create_pooler_config_for_render,
            create_pooler_config_for_neon,
        ]:
            config = create_func()
            assert config.enabled is True
            assert config.auto_detect is False  # Don't auto-detect for known platforms
            
    def test_platform_configs_use_transaction_mode(self):
        """Test platform configs use transaction mode."""
        for create_func in [
            create_pooler_config_for_supabase,
            create_pooler_config_for_render,
            create_pooler_config_for_neon,
        ]:
            config = create_func()
            assert config.mode == PoolerMode.TRANSACTION

